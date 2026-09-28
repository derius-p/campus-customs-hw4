"""Tidy views of messy catalog data, shared by the website filters and the agent's search.

- category_for: the database has 22 spellings of garment types ("short-sleeve T-shirt",
  "short-sleeve t-shirt", "t-shirt", ...). These map to 6 shopper-friendly categories.
- color_family: 22 color names ("heather gray", "dark heather charcoal", ...) map to
  simple families (Gray, Navy, ...), so "gray" finds every shade of gray.
- expand_aliases / correct_spelling: Yale nicknames ("JE", "TD", "BK", "The Game") and
  typos ("hoody", "davenprt") are turned into words that appear in the catalog.
"""

from __future__ import annotations

import difflib
import re

# ---- categories ------------------------------------------------------------------------

CATEGORIES = ["T-shirts", "Crewnecks & sweatshirts", "Hoodies", "Quarter-zips", "Jackets & fleece", "Long sleeve & performance"]


def category_for(garment_type: str) -> str:
    g = garment_type.lower()
    if "quarter-zip" in g or "quarter zip" in g:
        return "Quarter-zips"
    if "hood" in g:
        return "Hoodies"
    if "jacket" in g or "fleece" in g:
        return "Jackets & fleece"
    if "t-shirt" in g or "tee" in g:
        return "T-shirts"
    if "performance" in g:
        return "Long sleeve & performance"
    return "Crewnecks & sweatshirts"  # crewneck, sweatshirt, mockneck


# ---- colors ----------------------------------------------------------------------------

COLOR_FAMILIES = ["Navy", "Blue", "Gray", "White", "Black", "Red", "Gold", "Green", "Multicolor"]
_COLOR_WORDS = [  # checked in order; first match wins
    ("navy", "Navy"), ("royal blue", "Blue"), ("light blue", "Blue"), ("blue", "Blue"),
    ("charcoal", "Gray"), ("gray", "Gray"), ("grey", "Gray"),
    ("white", "White"), ("cream", "White"), ("ivory", "White"),
    ("black", "Black"), ("red", "Red"), ("coral", "Red"),
    ("gold", "Gold"), ("yellow", "Gold"), ("green", "Green"), ("multi", "Multicolor"),
]


def color_family(color: str) -> str:
    c = color.lower()
    for word, family in _COLOR_WORDS:
        if word in c:
            return family
    return color.title()


def color_families(colors: list[str]) -> list[str]:
    return list(dict.fromkeys(color_family(c) for c in colors))


# ---- nicknames and typos (agent search) -------------------------------------------------

# Yale shorthand -> words found in product names and tags. Keys are lowercase; multi-word
# keys are matched as phrases before the query is split into words.
ALIASES = {
    "je": "jonathan edwards", "jonathan edwards": "jonathan edwards",
    "td": "timothy dwight", "timothy dwight": "timothy dwight",
    "bk": "berkeley", "bf": "benjamin franklin", "ben franklin": "benjamin franklin", "franklin": "benjamin franklin",
    "gh": "grace hopper", "hopper": "grace hopper", "calhoun": "grace hopper",
    "dport": "davenport", "d'port": "davenport", "sy": "saybrook", "tc": "trumbull", "mc": "morse",
    "pc": "pierson", "br": "branford",
    "the game": "harvard", "harvard game": "harvard", "h-y": "harvard", "hy game": "harvard",
    "som": "school of management", "ysm": "school of medicine", "yls": "law school", "law": "law school",
    "ysph": "school of public health", "seas": "school of engineering", "div school": "divinity school",
    "yale bowl": "bowl", "bulldogs": "bulldog", "handsome dan": "bulldog",
    "sweats": "sweatshirt", "zip-up": "zip", "zipup": "zip", "quarter zip": "quarter-zip", "1/4 zip": "quarter-zip",
    "q-zip": "quarter-zip", "grandmother": "grandma", "grandfather": "grandpa", "mother": "mom", "father": "dad",
    "mum": "mom", "sibling": "brother",
}
_PHRASES = sorted((k for k in ALIASES if " " in k or "-" in k or "/" in k or "'" in k), key=len, reverse=True)


def expand_aliases(text: str) -> tuple[str, list[str]]:
    """Replace Yale nicknames with catalog words. Returns (new text, notes like 'JE → jonathan edwards')."""
    notes: list[str] = []
    out = f" {text.lower()} "
    for phrase in _PHRASES:
        pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
        if re.search(pattern, out):
            out = re.sub(pattern, f" {ALIASES[phrase]} ", out)
            notes.append(f"{phrase} → {ALIASES[phrase]}")
    words = []
    for word in out.split():
        if word in ALIASES and ALIASES[word] != word:
            words.append(ALIASES[word])
            notes.append(f"{word} → {ALIASES[word]}")
        else:
            words.append(word)
    return " ".join(words), notes


def correct_spelling(word: str, vocabulary: set[str]) -> str | None:
    """The closest catalog word for a likely typo, or None. Short words are left alone."""
    if len(word) < 4 or word in vocabulary or word.isdigit():
        return None
    match = difflib.get_close_matches(word, vocabulary, n=1, cutoff=0.8)
    return match[0] if match else None


# ---- themes (for "similar items") ------------------------------------------------------

THEME_GROUPS = {
    "residential college": [
        "benjamin franklin", "berkeley", "branford", "davenport", "ezra stiles", "grace hopper",
        "jonathan edwards", "morse", "pauli murray", "pierson", "saybrook", "silliman", "timothy dwight", "trumbull",
    ],
    "graduate school": [
        "school of architecture", "school of art", "school of engineering", "school of management",
        "school of medicine", "school of music", "school of nursing", "school of public health",
        "divinity school", "law school", "forest school",
    ],
    "sport": [
        "field hockey", "hockey", "baseball", "basketball", "football", "soccer", "tennis", "golf",
        "diving", "swimming", "sailing", "fencing", "squash", "lacrosse", "volleyball", "track",
        # "crew" (rowing) is detected from an exact "Crew" tag in tools._themes, since "crew neck" is a collar style
    ],
    "family": ["grandma", "grandpa", "mom", "dad", "aunt", "uncle", "brother", "sister", "cousin"],
}
_GROUP_LABELS = {
    "residential college": "another residential college design",
    "graduate school": "another graduate school design",
    "sport": "another Yale sport",
    "family": "another family gift",
}


def themes_of(text: str) -> dict[str, str]:
    """{group: specific theme} found in a product's name and tags, e.g. {"residential college": "davenport"}."""
    t = f" {re.sub(r'[^a-z ]+', ' ', text.lower())} "
    found: dict[str, str] = {}
    for group, names in THEME_GROUPS.items():
        for name in names:  # longer names first within each list, e.g. "field hockey" before "hockey"
            if f" {name} " in t:
                found[group] = name
                break
    return found


def group_label(group: str) -> str:
    return _GROUP_LABELS[group]
