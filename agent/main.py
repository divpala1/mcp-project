"""
Agent entrypoint.

    python -m agent.main "your prompt here"

For a full step-by-step explanation of this file and how all the agent modules
connect, see agent/WALKTHROUGH.md.

What this file demonstrates (learning checkpoint #6 — streaming):

    `astream_events(version="v2")` is the event bus LangGraph exposes.
    It emits heterogeneous events as the graph runs:

        on_chat_model_start      LLM call is starting
        on_chat_model_stream     one chunk per token as the LLM generates
        on_chat_model_end        LLM call finished (full message available)
        on_tool_start            a ToolNode is invoking a tool
        on_tool_end              the tool returned (or raised)
        on_chain_start / _end    graph-node boundaries

    In production UIs this is what drives the "thinking...", "using tool…",
    and token-by-token rendering users see. Here we just print them —
    replace `print` with websocket-push / SSE-yield for a real front-end.
"""
from __future__ import annotations

import asyncio
import logging
import sys

from agent.agent import build_agent
from agent.llm import get_llm
from agent.observability import setup_tracing
from agent.tools import build_mcp_client, load_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
# langchain-mcp-adapters + httpx log at DEBUG level by default; quiet to WARNING
# to keep the agent's own output readable.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)

log = logging.getLogger("agent.main")


async def run(prompt: str) -> None:
    setup_tracing()

    llm = get_llm()
    log.info("LLM ready: %s", type(llm).__name__)

    client = build_mcp_client()
    tools = await load_tools(client)

    agent = build_agent(llm, tools)
    log.info("Agent compiled with %d tools", len(tools))

    print()
    print("=" * 72)
    print(f"▶ USER: {prompt}")
    print("=" * 72)
    print()

    # Track whether we're currently streaming assistant text, so we can
    # render tool-call boundaries on their own lines without mid-token cuts.
    in_text = False

    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": prompt}]},
        version="v2",
    ):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            # chunk.content is a string for most providers; some return lists
            # of content blocks (Anthropic-style). Normalise to str.
            text = chunk.content if isinstance(chunk.content, str) else "".join(
                b.get("text", "") for b in chunk.content if isinstance(b, dict)
            )
            if text:
                if not in_text:
                    print("🤖 ", end="", flush=True)
                    in_text = True
                print(text, end="", flush=True)
        elif kind == "on_tool_start":
            if in_text:
                print()
                in_text = False
            name = event.get("name", "<tool>")
            args = event["data"].get("input", {})
            print(f"⚙  {name}({_short(args)})")
        elif kind == "on_tool_end":
            name = event.get("name", "<tool>")
            out = event["data"].get("output")
            print(f"   → {_short(out)}")
            print()

    print()
    print("=" * 72)


def _short(obj: object, limit: int = 240) -> str:
    """Truncate any repr to a single line of at most `limit` chars."""
    s = repr(obj)
    s = s.replace("\n", " ")
    return s if len(s) <= limit else s[:limit] + "…"


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: python -m agent.main "your prompt"', file=sys.stderr)
        sys.exit(2)
    prompt = " ".join(sys.argv[1:])
    asyncio.run(run(prompt))


if __name__ == "__main__":
    main()
