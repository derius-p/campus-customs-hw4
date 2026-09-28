"""Pydantic and PydanticAI types shared by the API, the agent, and its tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

# ---- products ------------------------------------------------------------------------


class ProductCard(BaseModel):
    """A product card for the chat or the results page; links to the single-item page."""

    product_id: str
    name: str
    garment_type: str
    description: str
    price: float
    image_url: str
    image_tone: str = "light"  # "dark" or "light" photo background, for styling the tile
    url: str  # site page for the product, e.g. /products/basic-hoodie-big-yale
    colors: list[str]
    sizes_in_stock: list[str]
    total_in_stock: int


class PageResults(BaseModel):
    """Search results the website shows on the main page (Products page)."""

    title: str  # e.g. "Navy hoodies in XL"
    products: list[ProductCard]


# ---- chat API (website <-> FastAPI) --------------------------------------------------


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class PageContext(BaseModel):
    """What the customer is looking at when they send a message (sent by the website)."""

    path: str = Field(default="/", max_length=300)  # e.g. /products/basic-hoodie-big-yale
    product_id: str | None = Field(default=None, max_length=120)  # set on a single-item page
    results_title: str | None = Field(default=None, max_length=120)  # set when viewing chat results


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # Earlier turns, oldest first. Used for guests only; signed-in history comes from the database.
    history: list[ChatTurn] = Field(default_factory=list, max_length=40)
    page: PageContext = Field(default_factory=PageContext)


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list)  # top picks, shown in the chat
    page_results: PageResults | None = None  # fuller set, shown on the main page
    saved: bool = False  # true when the exchange was stored in the customer's history


class HistoryMessage(BaseModel):
    """One saved message, as the chat widget shows it when a customer returns."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    page_results: PageResults | None = None
    created_at: str


class ChatHistoryResponse(BaseModel):
    messages: list[HistoryMessage]


# ---- tool results (what the agent sees) ---------------------------------------------
# Everything here comes straight from the catalogue and inventory tables at the moment
# the tool runs; the status labels are computed from inventory.quantity.

StockStatus = Literal["in stock", "low stock", "out of stock"]
LOW_STOCK_MAX = 3  # 1-3 units left counts as low stock


def stock_status(quantity: int) -> StockStatus:
    if quantity <= 0:
        return "out of stock"
    return "low stock" if quantity <= LOW_STOCK_MAX else "in stock"


class SizeStock(BaseModel):
    """Stock for one size of one product (one inventory row)."""

    size: str
    quantity: int = Field(description="Units on hand right now (inventory.quantity).")
    status: StockStatus


class ProductSummary(BaseModel):
    """A search hit: enough to compare options. Call get_product_info for full detail."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str]
    sizes_in_stock: list[str]
    sizes_out_of_stock: list[str]
    total_in_stock: int
    description: str


class ProductSearchResult(BaseModel):
    query: str
    interpreted_as: str | None = Field(
        default=None, description='Nicknames or typos that were translated, e.g. "JE → jonathan edwards, hoody → hoodie".'
    )
    filters: dict[str, str | float] = Field(default_factory=dict)
    total_matches: int
    products: list[ProductSummary]
    note: str | None = None


class SimilarItem(ProductSummary):
    why_similar: list[str] = Field(description='Plain reasons, e.g. ["same style: Hoodies", "also Davenport"].')


class SimilarItemsResult(BaseModel):
    """In-stock alternatives to one product (e.g. when the customer's size is sold out)."""

    based_on: str  # name of the original product
    size: str | None  # only items with this size in stock, if given
    items: list[SimilarItem]
    note: str | None = None


class ProductInfo(BaseModel):
    """Full, current facts for one product from the database."""

    product_id: str
    name: str
    garment_type: str
    description: str
    price: float
    colors: list[str]
    stock_by_size: list[SizeStock]
    total_in_stock: int
    sizes_out_of_stock: list[str]
    availability: str = Field(description="One-line stock summary to relay to the customer.")
    requested_size: SizeStock | None = Field(
        default=None, description="Stock for the size the customer asked about, if one was given."
    )
    matched_by: Literal["product_id", "name", "closest name"]
    similar_in_stock: list[SimilarItem] = Field(
        default_factory=list,
        description="When the requested size is out of stock: up to 3 alternatives that have that size. Offer them.",
    )


class ProductNotFound(BaseModel):
    """Returned when no product matches; never guess a product from this."""

    looked_up: str
    message: str
    suggestions: list[str] = Field(default_factory=list, description="Names of the closest products, if any.")


# ---- agent (PydanticAI) --------------------------------------------------------------


class AgentPageResults(BaseModel):
    """Search results for the main page, chosen by the agent."""

    title: str = Field(description='Short plain heading for the results, e.g. "Navy hoodies in XL".')
    product_ids: list[str] = Field(
        description="product_id values of ALL good matches from search results (up to 36), best first."
    )


class AgentReply(BaseModel):
    """What the agent must return each turn (its structured output)."""

    message: str = Field(description="The reply to show the customer, in Markdown.")
    product_ids: list[str] = Field(
        default_factory=list,
        description=(
            "product_id values (from tool results) of the top products to show as cards in the chat, "
            "up to 6, best first. Empty if no products are relevant."
        ),
    )
    page_results: AgentPageResults | None = Field(
        default=None,
        description=(
            "Set when the customer is searching or browsing for options, so all matches appear on the "
            "main page. Leave null for questions about one specific product, small talk, or no matches."
        ),
    )


@dataclass
class ViewedProduct:
    """The product on the page the customer is viewing, looked up from the database."""

    product_id: str
    name: str
    price: float


@dataclass
class ChatDeps:
    """Per-request context for the agent. Customer fields are limited to name and email;
    never password hashes or session tokens."""

    user_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    page_path: str = "/"
    viewing: ViewedProduct | None = None  # set when the customer is on a single-item page
    results_title: str | None = None  # set when the customer is looking at chat results
    history_note: str | None = None  # when their saved messages are from, e.g. "6 saved messages from Sep 19, 2026"
