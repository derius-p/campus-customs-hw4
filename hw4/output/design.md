# Campus Customs Storefront Design

Goal: make the site feel like the real Yale Bulldog Blue shop, so visitors trust it, stay longer, and find something to buy.

## What we changed and why

| Area | What changed | Why it helps customers stick around and buy |
|---|---|---|
| **Brand identity** | Header and footer use the official Yale Bulldog Blue lockup: athletic slab "YALE" (centered) over "BULLDOG BLUE" in condensed caps, a rule, and "BY CAMPUS CUSTOMS". The crest is the athletic Yale "Y" (traced from the official logo, symmetric) in white on Yale Blue inside a thin white ring, also used as the chat avatar. | Instantly recognizable as Yale, and consistent with the store's real logo and the lettering on the clothes. Recognition builds trust, which matters when paying for licensed gear. |
| **Fonts** | Yale's own typeface (YaleNew, Matthew Carter) for headings and prices; varsity-style Oswald capitals for labels, navigation, and badges; Inter for body text. | Headings feel like Yale; small caps echo athletic lettering; a clean body font keeps descriptions and stock easy to read. |
| **Color** | Yale Blue and a deep navy on warm ivory, a light blue accent, and stock colors: green in stock, amber low, red sold out. | A calm, premium palette that matches the product photos; stock status is readable at a glance, so shoppers don't waste clicks on sold-out items. |
| **Hierarchy** | Announcement bar (officially licensed · 57 Broadway · ask our assistant) → navigation → home page in buying order: hero with "Shop All" → **Find your fit** category tiles with counts → **Campus classics** best sellers → **Shop by story** (college, game day, family, grad schools) → trust strip → footer. | Moves visitors from "what is this?" to a product in two clicks, with several entry points for different shoppers (browsing by type, by gift, by college). |
| **Product presentation** | Photos with black side bars are trimmed and re-squared (`backend/prepare_images.py`), and each sits on a tile matching its own background, filling the frame. Cards show category, name, price, color swatches, and a badge ("All sizes", "Only 2 sizes left", "Sold out"); hover zooms the photo and shows "View details →". Product pages have a large photo, a live stock line, color chips, clickable size buttons (sold-out struck through, low stock marked), a message showing how many are left, and "Ask about this item". | Clean, consistent photos make the catalog look professional. Swatches, badges, and size buttons answer "does it come in my color and size?" before the shopper has to ask, and "Only 2 left" adds gentle urgency. |
| **Motion** | Sections and cards fade up in sequence; hero photos float; cards lift on hover; the chat button pulses briefly on arrival and the panel springs open; new messages slide in; a three-dot typing indicator. All motion turns off for "reduce motion" users. | Makes the site feel alive and responsive and draws the eye to the chat and products, without getting in the way. |
| **Chat feel** | Branded header (Yale "Y" avatar, "Online · checks live stock"), rounded message bubbles, product cards with scroll arrows, suggestion chips, "See all on the page", and a friendlier "Ask us anything" button. "Shop by story" tiles and "Ask about this item" send questions straight to the chat. | The assistant feels like part of the store, not a bolt-on. More people use it, and it steers them to in-stock products they can buy. |
| **Copy** | Original Home and About text; the shop is described as "in the commercial heart of Yale at 57 Broadway"; claims kept to what's true (e.g. "from Berkeley to Trumbull", since the catalog has 11 of the 14 colleges). | Honest, confident, local wording supports trust. |

## Notes

- Yale typeface files (`frontend/public/fonts/`) and the official logo lettering (`frontend/public/brand/`) are used as a licensed Yale retailer. They're excluded from git, so they need to be copied in when setting up the project elsewhere.
- Original product photos in `data/products/` are unchanged; tidied display copies are in `data/products_display/`.
- Main files: `frontend/src/index.css` (styles), `components/BrandLockup.tsx`, `components/YaleY.tsx`, `components/ProductCard.tsx`, `pages/Home.tsx`, `pages/ProductDetail.tsx`.
