"""Tools the Campus Customs agent can call, plus catalog helpers used by the API.

The tools only read the catalogue and inventory tables. They never touch users,
passwords, or sessions, so the agent has no way to reveal account data.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic_ai import RunContext

from catalog import (
    ALIASES,
    category_for,
    color_families,
    color_family,
    correct_spelling,
    expand_aliases,
    group_label,
    themes_of,
)
from db import connect, image_info
from models import (
    ChatDeps,
    ProductCard,
    ProductInfo,
    ProductNotFound,
    ProductSearchResult,
    ProductSummary,
    SimilarItem,
    SimilarItemsResult,
    SizeStock,
    ViewedProduct,
    stock_status,
)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
MAX_RESULTS = 36  # enough to fill the results page

# Words customers use -> words in the catalog.
_SYNONYMS = {
    "tee": "t-shirt", "tees": "t-shirt", "tshirt": "t-shirt", "tshirts": "t-shirt", "shirt": "t-shirt",
    "hoodies": "hoodie", "hooded": "hoodie", "hood": "hoodie", "hoody": "hoodie", "hoodys": "hoodie", "hoodey": "hoodie",
    "crew": "crewneck", "crewnecks": "crewneck", "sweatshirts": "sweatshirt",
    "quarterzip": "quarter-zip", "1/4": "quarter-zip", "zip": "zip",
    "jackets": "jacket", "fleeces": "fleece", "sweater": "fleece",
    "grey": "gray", "navy": "navy",
}
_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "in", "of", "to", "do", "you", "have", "any",
    "i", "me", "my", "want", "need", "looking", "some", "something", "show", "yale", "is", "are", "it",
    # "gift" describes the purpose, not the product; any item can be a gift
    "gift", "gifts", "present", "presents", "idea", "ideas", "under", "below", "less", "than",
}


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9/'-]+", text.lower())
    return [_SYNONYMS.get(w, w) for w in words if w not in _STOPWORDS]


def _vocabulary(catalog: list[dict[str, Any]]) -> set[str]:
    """Every word that appears in the catalog, for typo correction."""
    words: set[str] = set()
    for p in catalog:
        text = " ".join([p["name"], p["garment_type"], p["description"], *p["search_tags"], *p["colors"]])
        words.update(w for w in _tokens(text) if len(w) >= 4)
    return words


def _query_terms(query: str, catalog: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Search words for a customer query, with Yale nicknames expanded and typos fixed.
    Returns (terms, notes describing any changes)."""
    text, notes = expand_aliases(query)
    single_aliases = {k for k in ALIASES if k.isalpha() and len(k) >= 4}
    vocabulary = _vocabulary(catalog) | single_aliases
    terms = []
    for word in _tokens(text):
        fixed = correct_spelling(word, vocabulary)
        if fixed:
            notes.append(f"{word} → {fixed}")
            word = fixed
        if word in single_aliases and ALIASES[word] != word:  # e.g. a typo of "grandfather"
            notes.append(f"{word} → {ALIASES[word]}")
            terms.extend(_tokens(ALIASES[word]))
        else:
            terms.append(word)
    return terms, notes


def _has_color(product: dict[str, Any], color: str) -> bool:
    """Exact shade ("heather gray") or family ("grey" finds every gray)."""
    return any(color.lower() in c.lower() for c in product["colors"]) or color_family(color) in product["color_families"]


def _stock(conn, product_id: str) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)).fetchall()
    order = {s: i for i, s in enumerate(SIZE_ORDER)}
    return sorted(({"size": r["size"], "quantity": r["quantity"]} for r in rows), key=lambda s: order.get(s["size"], 99))


def _in_stock_sizes(stock: list[dict[str, Any]]) -> list[str]:
    return [s["size"] for s in stock if s["quantity"] > 0]


def _load_catalog() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM catalogue").fetchall()
        return [
            {
                "product_id": r["product_id"],
                "name": r["name"],
                "garment_type": r["garment_type"],
                "description": r["description"],
                "colors": json.loads(r["colors"]),
                "search_tags": json.loads(r["search_tags"]),
                "price": r["price"],
                "image_file_path": r["image_file_path"],
                "stock": _stock(conn, r["product_id"]),
                "category": category_for(r["garment_type"]),
                "color_families": color_families(json.loads(r["colors"])),
            }
            for r in rows
        ]


def _score(product: dict[str, Any], terms: list[str]) -> tuple[float, int]:
    """(relevance score, how many of the distinct search terms matched somewhere)."""
    fields = [
        (3.0, f"{product['name']} {product['garment_type']}"),
        (2.0, " ".join(product["search_tags"])),
        (2.0, " ".join(product["colors"])),
        (1.0, product["description"]),
    ]
    score = 0.0
    matched: set[str] = set()
    for weight, text in fields:
        words = set(_tokens(text))
        joined = " ".join(words)
        for term in terms:
            if term in words:
                score += weight
                matched.add(term)
            elif len(term) > 3 and term in joined:  # partial match, e.g. "davenport" in "davenport's"
                score += weight / 2
                matched.add(term)
    return score, len(matched)


# ---- agent tools ---------------------------------------------------------------------


def _size_stock(stock: list[dict[str, Any]]) -> list[SizeStock]:
    return [SizeStock(size=s["size"], quantity=s["quantity"], status=stock_status(s["quantity"])) for s in stock]


def _product_summary(product: dict[str, Any]) -> ProductSummary:
    stock = product["stock"]
    return ProductSummary(
        product_id=product["product_id"],
        name=product["name"],
        garment_type=product["garment_type"],
        price=product["price"],
        colors=product["colors"],
        sizes_in_stock=_in_stock_sizes(stock),
        sizes_out_of_stock=[s["size"] for s in stock if s["quantity"] <= 0],
        total_in_stock=sum(s["quantity"] for s in stock),
        description=product["description"],
    )


def search_products(
    ctx: RunContext[ChatDeps],
    query: str = "",
    color: str | None = None,
    size: str | None = None,
    max_price: float | None = None,
    limit: int = 8,
) -> ProductSearchResult:
    """Find products that match what the customer is looking for.

    Use this to discover options. For a specific product's price, description, or
    stock, call get_product_info.

    Args:
        query: What the customer wants in their words, e.g. "navy hoodie", "Davenport crewneck",
            "gift for my dad", "The Game". Leave empty to browse with filters only.
        color: Only products offered in this color, e.g. "gray".
        size: Only products with this size in stock: XS, S, M, L, XL, or XXL.
        max_price: Only products at or under this price in dollars.
        limit: How many results to return (1-36). Use 36 when collecting results for the page.
    """
    catalog = _load_catalog()
    terms, interpreted = _query_terms(query, catalog)
    size = size.strip().upper() if size else None
    results = []
    for product in catalog:
        if color and not _has_color(product, color):
            continue
        if max_price is not None and product["price"] > max_price:
            continue
        if size and size not in _in_stock_sizes(product["stock"]):
            continue
        score, covered = _score(product, terms) if terms else (1.0, 0)
        if score > 0:
            results.append((covered, score, product))
    # Products matching every search word come first; if any exist, weaker partial matches are dropped.
    distinct = len(set(terms))
    partial_note = None
    if distinct > 1 and any(r[0] == distinct for r in results):
        results = [r for r in results if r[0] == distinct]
    elif distinct > 1 and results:
        unmatched = [t for t in dict.fromkeys(terms) if not any(_score(p, [t])[0] > 0 for _, _, p in results)]
        partial_note = (
            "No product matches everything asked for"
            + (f" (nothing matches: {', '.join(unmatched)})" if unmatched else "")
            + ". These are only partial matches; tell the customer that first."
        )
    results.sort(key=lambda r: (-r[0], -r[1], r[2]["price"]))
    results = [(score, product) for _, score, product in results]
    limit = max(1, min(MAX_RESULTS, limit))
    filters = {k: v for k, v in {"color": color, "size": size, "max_price": max_price}.items() if v is not None}
    return ProductSearchResult(
        query=query,
        interpreted_as=", ".join(interpreted) or None,
        filters=filters,
        total_matches=len(results),
        products=[_product_summary(p) for _, p in results[:limit]],
        note="No products matched. Say so, and try broader words or fewer filters." if not results else partial_note,
    )


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _find_product(catalog: list[dict[str, Any]], product: str) -> tuple[dict[str, Any] | None, str, list[str]]:
    """Resolve a product_id or a product name. Returns (product, matched_by, suggestions)."""
    by_id = {p["product_id"]: p for p in catalog}
    if product.strip() in by_id:
        return by_id[product.strip()], "product_id", []
    wanted = _normalize(product)
    for p in catalog:
        if _normalize(p["name"]) == wanted or _normalize(p["product_id"]) == wanted:
            return p, "name", []
    # Closest name by shared words; only accept a clear, single winner.
    wanted_words = set(_tokens(product))
    scored = []
    for p in catalog:
        words = set(_tokens(p["name"]))
        overlap = len(wanted_words & words) / max(1, len(wanted_words | words))
        if overlap > 0:
            scored.append((overlap, p))
    scored.sort(key=lambda s: -s[0])
    suggestions = [p["name"] for _, p in scored[:3]]
    if scored and scored[0][0] >= 0.5 and (len(scored) == 1 or scored[0][0] > scored[1][0]):
        return scored[0][1], "closest name", []
    return None, "", suggestions


def get_product_info(ctx: RunContext[ChatDeps], product: str, size: str | None = None) -> ProductInfo | ProductNotFound:
    """Look up current facts for one product in the database: description, price, colors,
    and how many are in stock for each size.

    Call this for ANY question about a product's price, stock, sizes, or details, even if
    you saw the product earlier in the conversation, so the numbers are current.

    Args:
        product: The product_id from search results (preferred), e.g. "basic-hoodie-big-yale",
            or the product's name, e.g. "Basic Hoodie Big Yale".
        size: A size the customer asked about (XS, S, M, L, XL, XXL), to get that size's stock.
    """
    catalog = _load_catalog()
    found, matched_by, suggestions = _find_product(catalog, product)
    if found is None:
        return ProductNotFound(
            looked_up=product,
            message="No product in the database matches that. Don't guess; tell the customer and offer the suggestions or a search.",
            suggestions=suggestions,
        )

    stock = _size_stock(found["stock"])
    total = sum(s.quantity for s in stock)
    out = [s.size for s in stock if s.status == "out of stock"]
    low = [f"{s.size} ({s.quantity} left)" for s in stock if s.status == "low stock"]
    if total == 0:
        availability = "OUT OF STOCK in every size."
    else:
        parts = [f"{total} in stock across sizes {', '.join(s.size for s in stock if s.quantity > 0)}."]
        if out:
            parts.append(f"OUT OF STOCK in {', '.join(out)}.")
        if low:
            parts.append(f"Low stock: {', '.join(low)}.")
        availability = " ".join(parts)

    requested = None
    similar: list[SimilarItem] = []
    if size:
        wanted = size.strip().upper()
        requested = next((s for s in stock if s.size == wanted), None)
        if requested is None:
            availability += f" Size {size!r} is not a size we carry for this item (sizes: {', '.join(s.size for s in stock)})."
        elif requested.status == "out of stock":
            availability += f" Requested size {wanted} is OUT OF STOCK. See similar_in_stock for alternatives in {wanted}."
            similar = _similar(catalog, found, wanted, 3)
        else:
            availability += f" Requested size {wanted}: {requested.quantity} in stock."

    return ProductInfo(
        product_id=found["product_id"],
        name=found["name"],
        garment_type=found["garment_type"],
        description=found["description"],
        price=found["price"],
        colors=found["colors"],
        stock_by_size=stock,
        total_in_stock=total,
        sizes_out_of_stock=out,
        availability=availability,
        requested_size=requested,
        matched_by=matched_by,
        similar_in_stock=similar,
    )


def _themes(product: dict[str, Any]) -> dict[str, str]:
    found = themes_of(" ".join([product["name"], *product["search_tags"]]))
    if "sport" not in found and any(tag.strip().lower() == "crew" for tag in product["search_tags"]):
        found["sport"] = "crew"  # the rowing team, not a crew-neck collar
    return found


def _similar(catalog: list[dict[str, Any]], base: dict[str, Any], size: str | None, limit: int) -> list[SimilarItem]:
    """In-stock products most like `base`: same style, same or related theme, shared colors, similar price."""
    base_themes = _themes(base)

    scored = []
    for p in catalog:
        if p["product_id"] == base["product_id"]:
            continue
        in_stock = _in_stock_sizes(p["stock"])
        if (size and size not in in_stock) or not in_stock:
            continue
        reasons, score = [], 0.0
        if p["category"] == base["category"]:
            score += 3
            reasons.append(f"same style: {p['category']}")
        themes = _themes(p)
        for group, name in base_themes.items():
            if themes.get(group) == name:  # same college, sport, or family member
                score += 4
                reasons.append(f"also {name.title()}")
            elif group in themes:  # e.g. a different residential college
                score += 2
                reasons.append(group_label(group))
        colors = sorted(set(base["color_families"]) & set(p["color_families"]))
        if colors:
            score += 1
            reasons.append("comes in " + "/".join(colors).lower())
        if abs(p["price"] - base["price"]) <= 15:
            score += 1
            reasons.append("similar price")
        if score >= 3:  # at least the same style, or a shared theme plus something else
            scored.append((score, p, reasons))
    scored.sort(key=lambda s: (-s[0], abs(s[1]["price"] - base["price"])))
    return [SimilarItem(**_product_summary(p).model_dump(), why_similar=r) for _, p, r in scored[:limit]]


def find_similar_items(
    ctx: RunContext[ChatDeps], product: str, size: str | None = None, limit: int = 6
) -> SimilarItemsResult | ProductNotFound:
    """Find in-stock alternatives to a product: same style, same college/sport/theme,
    shared colors, similar price. Use when the customer's size is sold out, or they want
    "something like this".

    Args:
        product: The product_id (preferred) or name of the product to find alternatives for.
        size: Only suggest items with this size in stock (XS, S, M, L, XL, XXL).
        limit: How many alternatives to return (1-12).
    """
    catalog = _load_catalog()
    base, _, suggestions = _find_product(catalog, product)
    if base is None:
        return ProductNotFound(looked_up=product, message="No product matches that.", suggestions=suggestions)
    size = size.strip().upper() if size else None
    items = _similar(catalog, base, size, max(1, min(12, limit)))
    return SimilarItemsResult(
        based_on=base["name"],
        size=size,
        items=items,
        note=None if items else "No close in-stock alternatives found; offer a broader search instead.",
    )


AGENT_TOOLS = [search_products, get_product_info, find_similar_items]


# ---- helpers for the API -------------------------------------------------------------


def viewed_product(product_id: str) -> ViewedProduct | None:
    """The product a customer has open, if the id is real."""
    with connect() as conn:
        row = conn.execute("SELECT product_id, name, price FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    return ViewedProduct(product_id=row["product_id"], name=row["name"], price=row["price"]) if row else None


def product_cards(product_ids: list[str], limit: int = 6) -> list[ProductCard]:
    """Turn the agent's chosen ids into cards, dropping any id that isn't a real product."""
    catalog = {p["product_id"]: p for p in _load_catalog()}
    cards: list[ProductCard] = []
    for pid in dict.fromkeys(product_ids):  # de-duplicate, keep order
        product = catalog.get(pid)
        if product is None:
            continue
        cards.append(
            ProductCard(
                product_id=pid,
                name=product["name"],
                garment_type=product["garment_type"],
                description=product["description"],
                price=product["price"],
                image_url=image_info(product["image_file_path"])[0],
                image_tone=image_info(product["image_file_path"])[1],
                url=f"/products/{pid}",
                colors=product["colors"],
                sizes_in_stock=_in_stock_sizes(product["stock"]),
                total_in_stock=sum(s["quantity"] for s in product["stock"]),
            )
        )
        if len(cards) == limit:
            break
    return cards
