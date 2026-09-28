"""The Campus Customs chat agent: model, prompt, and tools wired together.

The model is reached through Portkey's OpenAI-compatible endpoint using
PORTKEY_API_KEY from HW4/.env. AGENT_MODEL overrides the default model.
The system prompt is read from prompts/prompt.md when the backend starts.
"""

from __future__ import annotations

import os

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, AgentRunResult, RunContext, UsageLimits
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from models import AgentReply, ChatDeps, ChatTurn
from tools import AGENT_TOOLS

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR.parent / ".env")

PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
MODEL_NAME = os.getenv("AGENT_MODEL", "gpt-5.6-luna")
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
MAX_MODEL_REQUESTS = 8  # model calls per customer message (each tool round trip + the final answer)
MAX_TOOL_CALLS = 12  # tool calls per customer message
MAX_HISTORY_TURNS = 20


def _model() -> OpenAIChatModel:
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is missing from HW4/.env")
    headers = {"x-portkey-api-key": key}
    if virtual_key := os.getenv("PORTKEY_VIRTUAL_KEY"):
        headers["x-portkey-virtual-key"] = virtual_key
    client = AsyncOpenAI(api_key=key, base_url=PORTKEY_BASE_URL, default_headers=headers)
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


@lru_cache(maxsize=1)
def get_agent() -> Agent[ChatDeps, AgentReply]:
    """Build the agent once, on first use."""
    agent = Agent(
        _model(),
        deps_type=ChatDeps,
        output_type=AgentReply,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        tools=AGENT_TOOLS,
        retries=2,
    )

    @agent.instructions
    def customer_context(ctx: RunContext[ChatDeps]) -> str:
        return describe_context(ctx.deps)

    return agent


def describe_context(deps: ChatDeps) -> str:
    """Per-message context added to the system prompt: who the customer is and what they see."""
    lines = ["# This conversation"]
    if deps.user_id:
        full_name = " ".join(n for n in (deps.first_name, deps.last_name) if n)
        lines.append(f"- The customer is signed in as {full_name} (email: {deps.email}).")
        if deps.history_note:
            lines.append(f"- Their saved chat history: {deps.history_note}. The most recent 20 messages are included above.")
        else:
            lines.append("- This is their first chat with us (no saved history yet).")
    else:
        lines.append("- The customer is browsing as a guest (not signed in). You don't know their name or email.")

    if deps.viewing:
        v = deps.viewing
        lines.append(
            f"- They are looking at the product page for **{v.name}** (product_id `{v.product_id}`, "
            f"${v.price:.2f}). If they say \"this\", \"it\", or \"this one\" without naming a product, they mean "
            f"this product: call get_product_info with product_id `{v.product_id}`."
        )
    elif deps.results_title:
        lines.append(f'- They are looking at the chat results page: "{deps.results_title}".')
    else:
        page = {"/": "the Home page", "/products": "the Products page (all products)", "/about": "the About Us page"}
        lines.append(f"- They are on {page.get(deps.page_path, 'page ' + deps.page_path)}; no single product is open.")
    return "\n".join(lines)


def _history(turns: list[ChatTurn]) -> list[ModelMessage]:
    """Earlier website chat turns as PydanticAI messages."""
    messages: list[ModelMessage] = []
    for turn in turns[-MAX_HISTORY_TURNS:]:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


async def run_chat(message: str, history: list[ChatTurn], deps: ChatDeps) -> AgentRunResult[AgentReply]:
    """Answer one customer message, given the conversation so far. Returns the full run result
    (output, messages, usage) so the API can write the audit trail."""
    return await get_agent().run(
        message,
        deps=deps,
        message_history=_history(history),
        usage_limits=UsageLimits(request_limit=MAX_MODEL_REQUESTS, tool_calls_limit=MAX_TOOL_CALLS),
    )
