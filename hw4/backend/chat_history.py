"""Saved chat history for signed-in customers, in the chat_messages table.

One row per message (customer or assistant):
    user_id            the customer (users.id)
    role               "user" or "assistant"
    content            the message text
    products_json      JSON list of the product cards shown with an assistant reply
    page_results_json  JSON {"title", "product_ids"} when a reply put search results
                       on the page (column added by ensure_schema)
    created_at         when it was sent

When history is loaded, product cards are rebuilt from their product_ids so prices and
stock are current, not the values at the time of the chat. Older rows (which stored
full product objects) load the same way.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from db import connect
from models import AgentPageResults, ChatTurn, HistoryMessage, PageResults, ProductCard
from tools import product_cards

DISPLAY_LIMIT = 60  # messages shown when a customer reopens the chat
AGENT_LIMIT = 20  # most recent messages given to the agent as context
PAGE_RESULTS_LIMIT = 36


def ensure_schema() -> None:
    with connect() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(chat_messages)")}
        if "page_results_json" not in columns:
            conn.execute("ALTER TABLE chat_messages ADD COLUMN page_results_json TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages (user_id, id)")


def save_exchange(
    user_id: int,
    user_text: str,
    reply_text: str,
    cards: list[ProductCard],
    page_results: AgentPageResults | None,
) -> None:
    """Store the customer's message and the assistant's reply."""
    page_json = (
        json.dumps({"title": page_results.title, "product_ids": page_results.product_ids}) if page_results else None
    )
    with connect() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'user', ?, '[]')",
            (user_id, user_text),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json, page_results_json) "
            "VALUES (?, 'assistant', ?, ?, ?)",
            (user_id, reply_text, json.dumps([c.model_dump() for c in cards]), page_json),
        )


def _rows(user_id: int, limit: int) -> list[Any]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, role, content, products_json, page_results_json, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return list(reversed(rows))  # oldest first


def _product_ids(products_json: str | None) -> list[str]:
    try:
        items = json.loads(products_json or "[]")
    except ValueError:
        return []
    return [item["product_id"] for item in items if isinstance(item, dict) and "product_id" in item]


def load_for_display(user_id: int) -> list[HistoryMessage]:
    """The customer's recent messages, with current product cards, for the chat widget."""
    messages = []
    for row in _rows(user_id, DISPLAY_LIMIT):
        page = None
        if row["page_results_json"]:
            data = json.loads(row["page_results_json"])
            cards = product_cards(data.get("product_ids", []), limit=PAGE_RESULTS_LIMIT)
            if cards:
                page = PageResults(title=data.get("title", "Results"), products=cards)
        messages.append(
            HistoryMessage(
                role=row["role"],
                content=row["content"],
                products=product_cards(_product_ids(row["products_json"])) if row["role"] == "assistant" else [],
                page_results=page,
                created_at=row["created_at"],
            )
        )
    return messages


def visit_summary(user_id: int) -> str | None:
    """When the customer chatted before, e.g. "12 saved messages from Sep 19, 2026 to Sep 27, 2026"."""
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) n, MIN(created_at) first, MAX(created_at) last FROM chat_messages WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row["n"]:
        return None
    fmt = lambda ts: datetime.strptime(ts[:10], "%Y-%m-%d").strftime("%b %d, %Y")  # noqa: E731
    span = fmt(row["first"]) if fmt(row["first"]) == fmt(row["last"]) else f"{fmt(row['first'])} to {fmt(row['last'])}"
    return f"{row['n']} saved messages from {span} (UTC dates); today is {datetime.now(timezone.utc):%b %d, %Y}"


def load_for_agent(user_id: int) -> list[ChatTurn]:
    """The most recent turns as plain text, for the agent's conversation memory."""
    return [ChatTurn(role=row["role"], content=row["content"][:4000]) for row in _rows(user_id, AGENT_LIMIT)]


def clear(user_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
