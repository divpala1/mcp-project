"""
Framework-free agent entry point.

This is the seam every host uses — CLI, FastAPI, tests. It knows nothing
about HTTP, SSE response framing, request schemas, or argv. It accepts
plain Python inputs (prompt + auth token + optional MCP server override),
runs one turn of the agent, and yields structured `AgentEvent` dicts.

Each caller decides how to render the events:
    - CLI (agent/main.py)   → print() with emoji markers, current behavior.
    - FastAPI (agent/api.py) → format as SSE `data:` frames, stream to client.
    - Tests / scripts        → assert on event sequence and content.

Why an async generator (not a list, not a callback):
    LangGraph's `astream_events` is itself an async iterator that emits
    incrementally. Buffering it into a list would defeat the whole point
    (token-by-token UX). A callback-based API would force every host into
    the same control-flow shape. An async generator is the universal
    consumer-friendly form — you can `async for ev in run_agent(...)` from
    any async context.

# NOTE(memory): when long-term / per-conversation memory lands, this is
# the function that grows extra inputs (`session_id`, `user_id`) and the
# message history will be loaded from a checkpointer instead of starting
# from a single HumanMessage. CLAUDE.md item #11.
"""
from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Literal, TypedDict

from agent.agent import build_agent
from agent.config import McpServerSpec, default_mcp_servers
from agent.llm import get_llm
from agent.observability import setup_tracing
from agent.tools import build_mcp_client, load_tools

log = logging.getLogger(__name__)


class AgentEvent(TypedDict, total=False):
    """
    Discriminated event union, encoded as a TypedDict for simplicity.

    `type` field decides which other fields are present:
        token        text: str
        tool_start   name: str, args: Any
        tool_end     name: str, output: Any
        error        message: str
        end          (no extra fields — terminator marker)

    Kept deliberately tiny. Fields can be added without breaking existing
    consumers since they read by key.
    """
    type: Literal["token", "tool_start", "tool_end", "error", "end"]
    text: str
    name: str
    args: Any
    output: Any
    message: str


async def run_agent(
    prompt: str,
    *,
    auth_token: str,
    mcp_servers: dict[str, McpServerSpec] | None = None,
) -> AsyncIterator[AgentEvent]:
    """
    Run the agent for one turn and yield structured events.

    Args:
        prompt: The user's message for this turn.
        auth_token: Bearer token forwarded to MCP servers. The MCP server
            validates and resolves to {user_id, org_id}; Qdrant filters
            scope to that org. The agent never inspects the token itself
            — it's an opaque pass-through.
        mcp_servers: Optional override of the server dict. If None, falls
            back to env-driven defaults via `default_mcp_servers()`.
            Production hosts that resolve servers per user/org pass a
            fully-formed dict here.

    Yields:
        AgentEvent dicts in the order they occur. Always terminated by an
        `end` event, even on error (an `error` event is emitted first).
    """
    setup_tracing()

    try:
        llm = get_llm()  # cached after first call
        servers = mcp_servers if mcp_servers is not None else default_mcp_servers()
        client = build_mcp_client(servers, auth_token=auth_token)
        tools = await load_tools(client)
        agent = build_agent(llm, tools)
        log.info("Agent compiled with %d tools", len(tools))

        # Track whether the previous emission was a streaming text chunk;
        # callers that render to a terminal use this to break lines around
        # tool boundaries. FastAPI/SSE consumers don't care — they just
        # forward each event verbatim.
        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": prompt}]},
            version="v2",
        ):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                # chunk.content is str on most providers; Anthropic-style
                # providers return a list of content blocks. Normalize.
                text = chunk.content if isinstance(chunk.content, str) else "".join(
                    b.get("text", "") for b in chunk.content if isinstance(b, dict)
                )
                if text:
                    yield {"type": "token", "text": text}
            elif kind == "on_tool_start":
                yield {
                    "type": "tool_start",
                    "name": event.get("name", "<tool>"),
                    "args": event["data"].get("input", {}),
                }
            elif kind == "on_tool_end":
                yield {
                    "type": "tool_end",
                    "name": event.get("name", "<tool>"),
                    "output": event["data"].get("output"),
                }
    except Exception as exc:
        # Surface errors as a structured event rather than letting the
        # generator raise. The two failures most worth surfacing here:
        #   - MCP handshake / auth rejection (bad bearer token → 401)
        #   - LLM provider error (rate limit, bad credentials)
        # In both cases the host (CLI / FastAPI) should display the
        # message; a traceback in the SSE stream is not useful to a UI.
        log.exception("Agent run failed")
        yield {"type": "error", "message": f"{type(exc).__name__}: {exc}"}
    finally:
        yield {"type": "end"}
