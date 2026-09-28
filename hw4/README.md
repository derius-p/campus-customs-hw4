# Campus Customs: Yale Bulldog Blue storefront with an AI shopping assistant

A customer-facing website for **Yale Bulldog Blue by Campus Customs** (officially licensed Yale apparel, 57 Broadway, New Haven) with a PydanticAI chatbot that answers from the store's real catalog and inventory.

- **Front end:** React + Vite + TypeScript (`frontend/`): Home, Shop (filters and sorting), product pages with live stock by size, About, Log in / Create Account, and a floating chat.
- **Back end:** FastAPI (`backend/`): product and image API, accounts with hashed passwords and sessions, and the chat agent.
- **Agent:** PydanticAI agent (`gpt-5.6-luna` via Portkey) with read-only tools to search products, look up price and stock by size, and suggest in-stock alternatives. Search results appear as cards in the chat and as a full grid on the page; signed-in customers' chats are saved; every agent run is logged to an append-only audit trail.

Full documentation: [`output/harness.md`](output/harness.md) (architecture, database, tools, models, safety, specs). Also see [`output/usability.md`](output/usability.md), [`output/design.md`](output/design.md), and [`output/app_check.html`](output/app_check.html).

## What's not in this repository

| Not included | Why | What to do |
|---|---|---|
| `.env` | Contains your private API key | Copy `.env.example` to `.env` and add your key |
| `data/campus_customs.db`, `data/products/` | Course data pack (database and product photos) | Place the data pack in `data/` (see below) |
| `frontend/public/fonts/`, `frontend/public/brand/` | Licensed Yale typeface and logo artwork | Optional. Without them the site uses fallback fonts and a text wordmark |

## Setup

Requirements: **Python 3.12+** (developed on 3.14) and **Node.js 20+** (developed on 24).

**1. Place the data pack** so the `data/` folder looks like this:

```
data/
├── campus_customs.db
└── products/
    ├── basic-hoodie-big-yale.jpg
    └── … (102 photos)
```

**2. Add your API key:**

```bash
cp .env.example .env
```

Then edit `.env` and set `PORTKEY_API_KEY=` to your Portkey key.

**3. Install the back end** (from the project folder):

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**4. Install the front end:**

```bash
cd frontend
npm install
cd ..
```

**5. Optional: tidy the product photos.** This trims black side bars so products fill their tiles. The originals are never changed.

```bash
cd backend
python prepare_images.py
cd ..
```

## Run

Use two terminals, both starting in the project folder.

**Terminal 1: back end** (API on http://127.0.0.1:8000)

```bash
source .venv/bin/activate
cd backend
uvicorn main:app --reload --port 8000
```

Wait for `Campus Customs agent ready (model gpt-5.6-luna)`.

**Terminal 2: front end** (site on http://localhost:5173)

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**. The front end forwards `/api` and `/media` requests to the back end, so both must be running.

**Test account:** `test@campuscustoms.yale.edu` / `password` (from the data pack), or create your own on the Create Account page.

**Try the chat:** "What hoodies do you have?" (results fill the page), "How much is the Basic Hoodie Big Yale, and how many in XL?", or, on the Davenport College Crewneck page, "Is this in a small?" (out of stock, with alternatives).

## Project layout

```
backend/
  main.py            FastAPI app: products, images, auth, chat, chat history
  agent.py           PydanticAI agent: model, prompt, tools, limits
  prompts/prompt.md  System prompt: voice, catalog rules, safety rules
  tools.py           Agent tools (read-only): search, product info, similar items
  models.py          Pydantic / PydanticAI types
  catalog.py         Categories, color families, Yale nicknames, typo fixes, themes
  auth.py            Accounts, password hashing, sessions, lockouts
  chat_history.py    Saved chats for signed-in customers
  audit.py           Append-only audit trail (output/audit_trail.json)
  db.py              Database connection and display-image lookup
  prepare_images.py  Makes tidied display copies of product photos
frontend/src/
  pages/             Home, Products, ProductDetail, About, Login, CreateAccount
  components/        NavBar, Footer, ChatWidget, ProductCard, ProductFilters, …
output/              harness.md, usability.md, design.md, app_check.html, audit_trail.json
data/                (data pack goes here)
```

## Configuration

Set in `.env` (see `.env.example`):

| Variable | Required | Default |
|---|---|---|
| `PORTKEY_API_KEY` | Yes | none |
| `AGENT_MODEL` | No | `gpt-5.6-luna` |
| `PORTKEY_BASE_URL` | No | `https://api.portkey.ai/v1` |
| `PORTKEY_VIRTUAL_KEY` | No | none |
| `COOKIE_SECURE` | No | off (set `1` when served over HTTPS) |
| `AUDIT_TRAIL_PATH` | No | `output/audit_trail.json` |
