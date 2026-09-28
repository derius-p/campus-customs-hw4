"""Append-only audit trail of every agent run, in output/audit_trail.json.

The file is a JSON array with one entry per customer message the agent handled:
when it ran, who asked (user id or guest; never email or passwords), what page they
were on, the message (shortened), each model request and tool call with short
arguments and a one-line result summary, token usage, and the stop reason.

Entries are only ever added. New entries are written just before the closing "]",
so earlier entries are never rewritten or removed, and the file stays valid JSON
for anyone who opens it. Delete the file by hand to start a new trail.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, ToolCallPart, ToolReturnPart

AUDIT_PATH = Path(os.getenv("AUDIT_TRAIL_PATH", Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"))
TEXT_LIMIT = 200  # characters kept from messages, arguments, and results
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _short(value: Any, limit: int = TEXT_LIMIT) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _summarize_result(content: Any) -> str:
    """One line describing a tool result, e.g. '27 matches: Basic Hoodie Big Yale, …'."""
    data = content.model_dump() if isinstance(content, BaseModel) else content
    if isinstance(data, dict):
        if "total_matches" in data:  # ProductSearchResult
            names = [p["name"] for p in data.get("products", [])[:3]]
            note = f" (note: {data['note']})" if data.get("note") else ""
            return _short(f"{data['total_matches']} matches: {', '.join(names)}{note}")
        if "availability" in data:  # ProductInfo
            return _short(f"{data['name']} ${data['price']:.2f}: {data['availability']}")
        if "items" in data and "based_on" in data:  # SimilarItemsResult
            return _short(f"{len(data['items'])} alternatives to {data['based_on']}: " + ", ".join(i["name"] for i in data["items"][:3]))
        if "looked_up" in data:  # ProductNotFound
            return _short(f"not found: {data['looked_up']}")
    return _short(data)


def _steps(messages: list[ModelMessage]) -> list[dict[str, Any]]:
    """Model requests and tool calls/results from this run, in order."""
    steps: list[dict[str, Any]] = []
    for message in messages:
        if isinstance(message, ModelResponse):
            calls = [p for p in message.parts if isinstance(p, ToolCallPart)]
            texts = [p.content for p in message.parts if isinstance(p, TextPart)]
            steps.append({
                "time": message.timestamp.isoformat(timespec="milliseconds"),
                "type": "model_response",
                "model": message.model_name,
                "finish_reason": getattr(message, "finish_reason", None),
                "tokens": {"input": message.usage.input_tokens, "output": message.usage.output_tokens},
                **({"text": _short(" ".join(texts))} if texts else {}),
            })
            for call in calls:
                if call.tool_name == "final_result":  # the structured answer, summarized under "output"
                    continue
                steps.append({"time": message.timestamp.isoformat(timespec="milliseconds"), "type": "tool_call",
                              "tool": call.tool_name, "args": _short(call.args)})
        elif isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, ToolReturnPart) and part.tool_name != "final_result":
                    steps.append({"time": part.timestamp.isoformat(timespec="milliseconds"), "type": "tool_result",
                                  "tool": part.tool_name, "result": _summarize_result(part.content)})
    return steps


def _append(entry: dict[str, Any]) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(entry, ensure_ascii=False, indent=2, default=str)
    with _lock:
        if not AUDIT_PATH.exists() or AUDIT_PATH.stat().st_size == 0:
            AUDIT_PATH.write_text("[\n" + text + "\n]\n", encoding="utf-8")
            return
        with open(AUDIT_PATH, "r+b") as f:
            # Find the closing "]" near the end and write the new entry in front of it.
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(size - 64, 0))
            tail = f.read()
            close = tail.rfind(b"]")
            if close < 0:
                raise OSError(f"{AUDIT_PATH} is not a JSON array; not modifying it")
            empty = tail[:close].rstrip().endswith(b"[")
            f.seek(size - len(tail) + close)
            f.truncate()
            f.write(((("\n" if empty else ",\n") + text + "\n]\n")).encode("utf-8"))


class RunAudit:
    """Collects one agent run and writes it to the trail when finished."""

    def __init__(self, *, user_id: int | None, page_path: str, message: str, model: str, limits: dict[str, int]):
        self.started = time.perf_counter()
        self.entry: dict[str, Any] = {
            "run_id": uuid.uuid4().hex[:12],
            "started_at": _now(),
            "user": f"user:{user_id}" if user_id else "guest",
            "page": page_path,
            "message": _short(message),
            "model": model,
            "limits": limits,
        }

    def finish(self, *, stop_reason: str, messages: list[ModelMessage] | None = None, output: Any = None,
               usage: Any = None, error: str | None = None) -> None:
        self.entry["steps"] = _steps(messages or [])
        tool_calls = [s["tool"] for s in self.entry["steps"] if s["type"] == "tool_call"]
        self.entry["tool_calls"] = tool_calls
        if output is not None:
            data = output.model_dump() if isinstance(output, BaseModel) else output
            page = data.get("page_results") or {}
            self.entry["output"] = {
                "reply": _short(data.get("message", "")),
                "chat_products": len(data.get("product_ids", [])),
                "page_results": {"title": page.get("title"), "products": len(page.get("product_ids", []))} if page else None,
            }
        if usage is not None:
            self.entry["usage"] = {"requests": usage.requests, "tool_calls": getattr(usage, "tool_calls", len(tool_calls)),
                                   "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}
        if error:
            self.entry["error"] = _short(error, 300)
        self.entry["stop_reason"] = stop_reason
        self.entry["finished_at"] = _now()
        self.entry["duration_ms"] = round((time.perf_counter() - self.started) * 1000)
        try:
            _append(self.entry)
        except OSError:
            pass  # never let logging break a customer's chat
