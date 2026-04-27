"""
MCP tool loading via `MultiServerMCPClient`.

─── Learning checkpoint #1: MCP session lifecycle ────────────────────────────

CLAUDE.md (and a lot of MCP tutorials written against langchain-mcp-adapters
0.1.x) says to run the agent *inside* an `async with client:` block. That
described the 0.1.x model: the client held one persistent session per
server for the lifetime of the block.

We're on 0.2.x, and the model inverted. The client is *stateless* — each
tool invocation opens a short-lived SSE session, does the JSON-RPC
round-trip, and closes. The LangChain tools returned by `get_tools()`
encapsulate that per-call session management. You can hold the tools past
the `get_tools()` call, past any block, and they still work.

The wire-level lifecycle per tool call is unchanged:

    1. GET  /mcp/sse         open an SSE stream (our auth middleware fires here)
    2. JSON-RPC: initialize  capability negotiation (protocol version etc.)
    3. JSON-RPC: tools/call  invoke the tool with validated arguments
    4. response event        result (or structured error) streams back
    5. connection close      teardown

This is why the auth header goes on the *connection config* (below): it
is sent on every SSE handshake, which happens on every tool call. Same
token flies across both servers — auth is a transport-layer concern
shared by the whole deployment (C1).

What an `async with client:` buys you in 0.2.x:
    It keeps a single persistent session per server open, so repeated
    tool calls skip the handshake overhead. For a learning project with
    a handful of tool calls per run, the per-call overhead is negligible
    and we don't bother. For a high-throughput agent you would wrap the
    whole agent run in the async-with block.

Tool schema conversion (learning checkpoint #3):
    MCP servers advertise tools as JSON Schema. langchain-mcp-adapters
    converts each to a `BaseTool` with pydantic-backed args validation
    and the MCP description as the LangChain tool description. That's
    what lets `llm.bind_tools([...])` (inside create_react_agent) accept
    MCP tools with zero glue code.
"""
from __future__ import annotations

import logging

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from agent.config import McpServerSpec

log = logging.getLogger(__name__)


def build_mcp_client(
    servers: dict[str, McpServerSpec],
    *,
    auth_token: str,
) -> MultiServerMCPClient:
    """
    Configure the client for the given server set, injecting the caller's
    bearer token on every SSE handshake.

    Why both args are caller-supplied (not read from env):
      - The bearer token must flow per-request so the user's identity
        reaches MCP / Qdrant for org-scoped retrieval (CLAUDE.md C1).
      - The server set is hybrid config: env defaults are assembled by
        `default_mcp_servers()` for the simple case, but production
        multi-tenant deployments resolve servers per user/org and pass
        the dict in directly.
      - Headers are baked into MultiServerMCPClient at construction in the
        0.2.x adapter, so per-request auth → per-request client. That's
        fine — client construction is cheap (no network I/O until the
        first tool call).
    """
    auth_header = {"Authorization": f"Bearer {auth_token}"}
    return MultiServerMCPClient({
        name: {**spec, "headers": auth_header}
        for name, spec in servers.items()
    })


async def load_tools(client: MultiServerMCPClient) -> list[BaseTool]:
    """
    Aggregate every server's tool list into one flat list.

    Namespacing (docs_* / notes_*) keeps names unique — we did it at the
    server side in Stages 2 and 3, so no disambiguation work here.
    """
    try:
        tools = await client.get_tools()
    except Exception as exc:
        # Surface which URLs were configured so the user knows where to look.
        urls = [cfg.get("url", "<unknown>") for cfg in client.connections.values()]
        log.error(
            "Failed to load MCP tools from %s: %s",
            ", ".join(urls) if urls else "<no servers>",
            exc,
            exc_info=True,
        )
        raise

    if not tools:
        log.warning("MCP client returned zero tools — agent will run toolless.")
    else:
        log.info(
            "Loaded %d MCP tools: %s",
            len(tools),
            ", ".join(t.name for t in tools),
        )
    return tools
