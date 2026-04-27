"""
Agent CLI entrypoint.

    AGENT_AUTH_TOKEN=tok_alice python -m agent.main "your prompt here"

For a full step-by-step explanation of this file and how all the agent modules
connect, see agent/WALKTHROUGH.md.

This file is a thin CLI wrapper around `agent.core.run_agent`. The real
work — LLM init, MCP client, ReAct graph, streaming — lives in
`agent/core.py`. Here we only:

    1. Read prompt from argv and bearer token from env.
    2. Iterate the structured `AgentEvent` stream.
    3. Render each event to the terminal (emoji markers + token-by-token
       text + tool call boundaries).

The bearer token comes from `AGENT_AUTH_TOKEN` env var rather than from a
flag because: (a) it's a credential, env is the right place; (b) it
mirrors how the FastAPI host receives it (an `Authorization` header is
just an env-var-shaped piece of identity for HTTP). In production this
env var doesn't exist — the FastAPI endpoint forwards the user's actual
header (see agent/api.py).

What this file demonstrates (learning checkpoint #6 — streaming):

    `astream_events(version="v2")` is the event bus LangGraph exposes,
    and `core.run_agent` translates it into a small set of
    consumer-friendly `AgentEvent` dicts. That translation is what lets
    CLI rendering and SSE streaming share the same upstream — every host
    iterates the same event stream, only the rendering differs.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

from agent.core import run_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
# langchain-mcp-adapters + httpx log at DEBUG level by default; quiet to WARNING
# to keep the agent's own output readable.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)

log = logging.getLogger("agent.main")


async def _print_stream(prompt: str, auth_token: str) -> None:
    print()
    print("=" * 72)
    print(f"▶ USER: {prompt}")
    print("=" * 72)
    print()

    # Track whether we're currently mid-text-stream. Lets us insert blank
    # lines around tool boundaries without breaking a token mid-stream.
    in_text = False

    async for event in run_agent(prompt, auth_token=auth_token):
        kind = event["type"]
        if kind == "token":
            if not in_text:
                print("🤖 ", end="", flush=True)
                in_text = True
            print(event["text"], end="", flush=True)
        elif kind == "tool_start":
            if in_text:
                print()
                in_text = False
            print(f"⚙  {event['name']}({_short(event['args'])})")
        elif kind == "tool_end":
            print(f"   → {_short(event['output'])}")
            print()
        elif kind == "error":
            if in_text:
                print()
                in_text = False
            print(f"⚠  ERROR: {event['message']}", file=sys.stderr)

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

    # CLI-only convenience. In production the FastAPI endpoint forwards
    # the caller's Authorization header instead — there is no AGENT_AUTH_TOKEN
    # env var in that deployment.
    token = os.getenv("AGENT_AUTH_TOKEN")
    if not token:
        print(
            "AGENT_AUTH_TOKEN env var is required for CLI use "
            "(must match a key in the MCP server's AUTH_TOKENS_JSON).",
            file=sys.stderr,
        )
        sys.exit(2)

    asyncio.run(_print_stream(prompt, token))


if __name__ == "__main__":
    main()
