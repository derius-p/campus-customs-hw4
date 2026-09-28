# Campus Customs Usability Improvements

Four improvements: two on the website (front end) and two in the backend/agent. Each was chosen to fix a problem we saw while building and testing the site.

| # | Improvement | Where | Helps |
|---|---|---|---|
| F1 | Filters and sorting on the Products page | Front end | Shopper and business |
| F2 | Suggested-question chips in the chat | Front end | Shopper and business |
| B1 | In-stock alternatives when a size is sold out | Backend / agent | Shopper and business |
| B2 | Search that understands Yale nicknames and typos | Backend / agent | Shopper and business |

---

## F1. Filters and sorting on the Products page

**What was added**

A filter bar above the product grid with five controls:

| Control | Options |
|---|---|
| Category | T-shirts, Crewnecks & sweatshirts, Hoodies, Quarter-zips, Jackets & fleece, Long sleeve & performance |
| Color | Navy, Blue, Gray, White, Black, Red, Gold, Green, Multicolor |
| In stock in | XS, S, M, L, XL, XXL (only products with that size available) |
| Price | Under $40, Under $60, Under $75 |
| Sort by | Name (A–Z), Price low to high, Price high to low, Most in stock |

The page shows "Showing 21 of 102 products", a "Clear filters" link, and a friendly message (pointing to the chat) when nothing matches. Filters are stored in the URL (e.g. `/products?category=Hoodies&size=XL&sort=price-asc`), so the Back button, refreshing, and sharing a link all keep them.

**How it works**

The database's labels are messy: 22 different garment-type spellings ("short-sleeve T-shirt", "short-sleeve t-shirt", "t-shirt"…) and 22 color names ("heather gray", "dark heather charcoal"…). `backend/catalog.py` maps these to the 6 categories and 9 color families above, and `GET /api/products` now returns each product's `category`, `color_families`, and `sizes_in_stock`. `GET /api/filters` provides the option lists. Filtering and sorting run in the browser (`frontend/src/components/ProductFilters.tsx`), so they're instant.

**Why it helps**

- **Shopper:** 102 products is a long scroll. A parent looking for an XL hoodie can go straight to the 21 that fit, and never lands on something they can't buy in their size (145 size combinations are sold out).
- **Business:** faster finding means more purchases and fewer customers giving up. "Most in stock" can steer shoppers toward items the shop has plenty of.

Tested: Hoodies + XL + price low to high showed 21 products starting at $45.00; adding Gray narrowed it to 8; Clear filters returned all 102 and kept the sort.

---

## F2. Suggested-question chips in the chat

**What was added**

A row of clickable question "chips" just above the chat's message box. One click sends the question. The chips change with the page the customer is on:

| Page | Chips |
|---|---|
| A product page | What sizes are in stock? · What colors does this come in? · Show me similar items |
| Chat results page | Which of these makes the best gift? · Only show ones in stock in L · What's the cheapest? |
| Anywhere else | Gifts under $50 · Hoodies in stock in XL · Residential college gear · Game day shirts |

**How it works**

`frontend/src/components/ChatWidget.tsx` picks the chip set from the same page context it already sends to the agent (Problem 8), so "What sizes are in stock?" on a product page is understood as "this product". Chips hide while the assistant is answering.

**Why it helps**

- **Shopper:** many people don't know what a store chatbot can do or how to phrase a question. Chips show useful things to ask and save typing, which is especially handy on phones.
- **Business:** more visitors use the assistant, and conversations start on product questions that lead to sales rather than off-topic chat. The chips also advertise features (similar items, stock by size, gift ideas).

Tested: on the Davenport crewneck page the chips switched to the product set; on About Us, clicking "Gifts under $50" put 30 items on the page with six top picks in the chat.

---

## B1. In-stock alternatives when a size is sold out

**What was added**

A new agent tool, `find_similar_items(product, size)`, and an automatic `similar_in_stock` list in `get_product_info` whenever the customer asks about a size that is out of stock. The agent now always follows "Size S is out of stock" with 2–3 alternatives in that size and a short reason for each, shown as product cards.

**How it works** (`backend/tools.py`, `backend/catalog.py`)

Each in-stock candidate is scored against the original product:

| Signal | Points | Example reason shown |
|---|---|---|
| Same category (style) | 3 | "same style: Crewnecks & sweatshirts" |
| Same college, sport, school, or family member | 4 | "also Hockey" |
| Related theme (a different residential college, sport, graduate school, or family member) | 2 | "another residential college design" |
| Shares a color family | 1 | "comes in gray/white" |
| Price within $15 | 1 | "similar price" |

Themes come from product names and tags (14 residential colleges, 11 graduate and professional schools, 17 sports, 9 family members). Only products with the requested size in stock are considered. `prompt.md` tells the agent to always offer these alternatives after an out-of-stock answer, and to use the tool for "something like this".

**Why it helps**

- **Shopper:** no dead end. Instead of "sorry, sold out", they immediately see options they can actually buy in their size.
- **Business:** saves sales that would otherwise be lost. With 145 sold-out size combinations, this comes up often. Suggestions stay on-theme (another college crewneck, another family hoodie), so they're likely to appeal.

Tested: "Is this in a small?" on the Davenport College Crewneck page: *"Size S is out of stock… Similar size-S options: Jonathan Edwards College Crewneck — another residential college crewneck in gray; Pierson College Crewneck; Grace Hopper College Crewneck"*, with cards. "Show me similar items" on the Yale Sports Hockey hoodie led with the Ice Hockey hoodie ("another Hockey hoodie").

---

## B2. Search that understands Yale nicknames and typos

**What was added**

`search_products` now translates Yale shorthand and fixes misspellings before searching, and reports what it changed (`interpreted_as`) so the agent can confirm lightly ("Here's what we have for Jonathan Edwards") without correcting the customer.

**How it works** (`backend/catalog.py`, used by `backend/tools.py`)

- **Nicknames and phrases** (about 50): college abbreviations (JE → Jonathan Edwards, TD → Timothy Dwight, BK → Berkeley, BF/Ben Franklin → Benjamin Franklin, D'port, Calhoun → Grace Hopper), schools (SOM, YLS, YSPH, SEAS), events ("The Game" → Harvard), and everyday words (sweats → sweatshirt, quarter zip / 1/4 zip → quarter-zip, grandfather → grandpa).
- **Typos:** any word not found in the catalog is matched to the closest catalog word (Python's `difflib`, 80% similarity; words under 4 letters are left alone), e.g. davenprt → davenport, crewnek → crewneck, saybrok → Saybrook, hodie → hoodie.
- **Color families:** a color filter of "grey" now finds every gray shade (51 products), not just products whose color text says "grey".
- **Gift words** ("gift", "present", "ideas") are treated as the purpose, not a product word, so "gifts under $50" means "anything under $50".

**Why it helps**

- **Shopper:** they can type the way Yale people actually talk, or make typos, and still get results. No need to know official product names.
- **Business:** fewer false "we don't carry that" answers when the shop does carry it, so fewer lost sales and less customer frustration.

Tested: "JE crewneck" → Jonathan Edwards College Crewneck; "TD" → Timothy Dwight College Crewneck; "BK quarter zip" → Berkeley 1/4 Zip; "crewnek for my granfather" → Yale Grandpa Crewneck; "dad hodie" → Yale Dad Hoodie. In chat, "any JE or TD crewnecks? also a davenprt hoody" found both crewnecks and correctly said there's no Davenport hoodie, offering the Davenport crewneck instead. Before this change, "gifts under $50" got "I didn't find a dedicated gift category"; now it returns all 30 items under $50.

---

## Data notes found along the way

- "School Of Architecture Crewneck" is actually a quarter-zip (its `garment_type` and description both say so); the filters follow the garment type, so it appears under Quarter-zips.
- Some products list a color that's only in the printed graphic (e.g. a heather gray hoodie with navy lettering lists "navy"), so a Navy color filter includes a few gray garments. Fixing this would mean separating garment color from print color in the database.
