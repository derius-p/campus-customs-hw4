"""Campus Customs backend: product catalog, images, accounts, and the chat agent.

Run from the backend folder (with the HW4 venv active):
    uvicorn main:app --reload --port 8000

Endpoints
    GET  /api/health                 quick check that the server is up
    GET  /api/products               all products with a short stock summary
    GET  /api/products/{product_id}  one product with stock by size
    GET  /api/filters                category, color, and size options for the Products page
    GET  /media/products/<file>.jpg  product images from data/products
    POST /api/auth/register          create an account (and sign in)
    POST /api/auth/login             sign in
    POST /api/auth/logout            sign out
    GET  /api/auth/me                the signed-in user, if any
    POST /api/chat                   send a chat message (+ page context); get the reply, top product
                                     cards for the chat, and (for searches) page_results for the page.
                                     Signed-in customers' messages are saved.
    GET  /api/chat/history           the signed-in customer's saved conversation
    DELETE /api/chat/history         erase it
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Cookie, FastAPI, HTTPException, Request
from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import auth
import chat_history
from catalog import CATEGORIES, COLOR_FAMILIES, category_for, color_families
from agent import MAX_HISTORY_TURNS, MAX_MODEL_REQUESTS, MAX_TOOL_CALLS, MODEL_NAME, get_agent, run_chat
from audit import RunAudit
from db import DATA_DIR, connect, image_info
from models import (
    AgentReply,
    ChatDeps,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    PageContext,
    PageResults,
)
from tools import product_cards, viewed_product

log = logging.getLogger("campus_customs")

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    auth.ensure_sessions_table()
    chat_history.ensure_schema()
    get_agent()  # load the prompt and model config at startup so problems show up immediately
    log.warning("Campus Customs agent ready (model %s)", MODEL_NAME)
    yield


app = FastAPI(title="Campus Customs API", lifespan=lifespan)

# The Vite dev server proxies /api and /media, but allow direct calls in development too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,  # session cookie
)
app.include_router(auth.router)

# Catalog image paths are stored relative to data/ (e.g. "products/x.jpg"),
# so they are served at /media/products/x.jpg. Only the images folder is
# exposed, never data/ itself (which holds the database).
app.mount("/media/products", StaticFiles(directory=DATA_DIR / "products"), name="media")
# Tidied copies (black side bars trimmed) from prepare_images.py, used for display when present.
if (DATA_DIR / "products_display").is_dir():
    app.mount("/media/display", StaticFiles(directory=DATA_DIR / "products_display"), name="media-display")


def product_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "image_url": image_info(row["image_file_path"])[0],
        "image_tone": image_info(row["image_file_path"])[1],  # "dark" or "light" photo background
        "price": row["price"],
    }


def size_key(size: str) -> int:
    return SIZE_ORDER.index(size) if size in SIZE_ORDER else len(SIZE_ORDER)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/products")
def list_products() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
            FROM catalogue c
            LEFT JOIN inventory i ON i.product_id = c.product_id
            GROUP BY c.product_id
            ORDER BY c.name
            """
        ).fetchall()
    with connect() as conn:
        stock = conn.execute("SELECT product_id, size FROM inventory WHERE quantity > 0").fetchall()
    in_stock: dict[str, set[str]] = defaultdict(set)
    for row in stock:
        in_stock[row["product_id"]].add(row["size"])
    products = []
    for r in rows:
        p = product_from_row(r)
        products.append({
            **p,
            "total_stock": r["total_stock"],
            # For the Products page filters: tidy category and color families, and sizes in stock.
            "category": category_for(r["garment_type"]),
            "color_families": color_families(p["colors"]),
            "sizes_in_stock": [s for s in SIZE_ORDER if s in in_stock[r["product_id"]]],
        })
    return products


@app.get("/api/filters")
def list_filters() -> dict[str, list[str]]:
    """Options for the Products page filters, in display order."""
    return {"categories": CATEGORIES, "colors": COLOR_FAMILIES, "sizes": SIZE_ORDER}


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        stock = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()
    inventory = sorted(
        ({"size": s["size"], "quantity": s["quantity"]} for s in stock), key=lambda s: size_key(s["size"])
    )
    return {**product_from_row(row), "inventory": inventory, "total_stock": sum(s["quantity"] for s in inventory)}


# ---- chat ------------------------------------------------------------------------------

BLOCKED_REPLY = "Sorry, I can't help with that. I'm here to help you find Campus Customs gear. What are you shopping for?"
LIMIT_REPLY = "Sorry, that one took me too many steps. Could you ask it a simpler way, or one item at a time?"
CRISIS_REPLY = (
    "I'm really sorry you're going through this. Please reach out now: call or text **988** "
    "(Suicide & Crisis Lifeline), or call **911** / Yale Police at **203-432-4400** if you're in danger. "
    "You don't have to handle this alone."
)
CRISIS_WORDS = re.compile(
    r"suicid|kill (?:myself|me)|hurt(?:ing)? myself|self[- ]?harm|end (?:it all|my life)|don'?t want to (?:live|be alive)|emergency|overdos",
    re.I,
)
PAGE_RESULTS_LIMIT = 36
CHAT_LIMIT, CHAT_WINDOW = 30, 5 * 60  # messages per client per 5 minutes (protects model spend)
_chat_times: dict[str, deque[float]] = defaultdict(deque)


def _rate_limited(request: Request) -> bool:
    client = request.client.host if request.client else "unknown"
    times = _chat_times[client]
    while times and times[0] < time.time() - CHAT_WINDOW:
        times.popleft()
    if len(times) >= CHAT_LIMIT:
        return True
    times.append(time.time())
    return False


def _deps(user: dict[str, Any] | None, page: PageContext) -> ChatDeps:
    """Agent context: the customer's name and email (if signed in) and what page they're on.
    The viewed product is looked up in the database, not taken from the browser's text."""
    deps = ChatDeps(page_path=page.path, results_title=page.results_title)
    if user:
        deps.user_id, deps.first_name, deps.last_name, deps.email = (
            user["id"], user["first_name"], user["last_name"], user["email"],
        )
        deps.history_note = chat_history.visit_summary(user["id"])
    if page.product_id:
        deps.viewing = viewed_product(page.product_id)
    return deps


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request, cc_session: str | None = Cookie(default=None)) -> ChatResponse:
    user = auth.current_user(cc_session)  # None for guests
    audit = RunAudit(
        user_id=user["id"] if user else None,
        page_path=body.page.path,
        message=body.message,
        model=MODEL_NAME,
        limits={"model_requests": MAX_MODEL_REQUESTS, "tool_calls": MAX_TOOL_CALLS, "history_turns": MAX_HISTORY_TURNS},
    )
    if _rate_limited(request):
        audit.finish(stop_reason="rate_limited")
        raise HTTPException(429, "You're sending messages quickly. Please wait a minute and try again.")
    deps = _deps(user, body.page)
    # Signed-in customers: memory comes from their saved history. Guests: from the browser.
    history = chat_history.load_for_agent(user["id"]) if user else body.history

    run = None
    with capture_run_messages() as messages:  # kept even if the run fails, for the audit trail
        try:
            run = await run_chat(body.message, history, deps)
        except UsageLimitExceeded as err:
            audit.finish(stop_reason="usage_limit", messages=list(messages), error=str(err))
            reply = AgentReply(message=LIMIT_REPLY)
        except ModelHTTPError as err:
            if "content_filter" not in str(err.body):
                audit.finish(stop_reason="error", messages=list(messages), error=f"ModelHTTPError {err.status_code}: {err.body}")
                log.exception("Agent failed")
                raise HTTPException(502, "Sorry, the assistant is having trouble right now. Please try again.")
            # The model provider's safety filter blocked the message (e.g. a jailbreak attempt,
            # or a message about self-harm, which gets crisis resources instead of a refusal).
            crisis = bool(CRISIS_WORDS.search(body.message))
            audit.finish(stop_reason="blocked_by_provider_filter", messages=list(messages),
                         error="content_filter" + ("; crisis resources shown" if crisis else ""))
            reply = AgentReply(message=CRISIS_REPLY if crisis else BLOCKED_REPLY)
        except Exception as err:
            audit.finish(stop_reason="error", messages=list(messages), error=f"{type(err).__name__}: {err}")
            log.exception("Agent failed")
            raise HTTPException(502, "Sorry, the assistant is having trouble right now. Please try again.")
    if run is not None:
        reply = run.output
        usage = run.usage() if callable(run.usage) else run.usage
        audit.finish(stop_reason="final_result", messages=run.new_messages(), output=reply, usage=usage)

    cards = product_cards(reply.product_ids)
    page_results = None
    if reply.page_results:
        page_cards = product_cards(reply.page_results.product_ids, limit=PAGE_RESULTS_LIMIT)
        if page_cards:  # only real products reach the page
            page_results = PageResults(title=reply.page_results.title, products=page_cards)

    saved = False
    if user:
        chat_history.save_exchange(user["id"], body.message, reply.message, cards, reply.page_results if page_results else None)
        saved = True
    return ChatResponse(reply=reply.message, products=cards, page_results=page_results, saved=saved)


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
def get_history(cc_session: str | None = Cookie(default=None)) -> ChatHistoryResponse:
    """The signed-in customer's saved conversation (most recent messages)."""
    user = auth.current_user(cc_session)
    if not user:
        raise HTTPException(401, "Log in to see your saved chat.")
    return ChatHistoryResponse(messages=chat_history.load_for_display(user["id"]))


@app.delete("/api/chat/history", status_code=204)
def delete_history(cc_session: str | None = Cookie(default=None)) -> None:
    """Let a signed-in customer erase their saved conversation."""
    user = auth.current_user(cc_session)
    if not user:
        raise HTTPException(401, "Log in to manage your saved chat.")
    chat_history.clear(user["id"])
