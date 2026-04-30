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

import asyncio
import logging

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from agent.config import McpServerSpec

log = logging.getLogger(__name__)

# ─── GitHub tool allowlist (C2a — tool explosion) ─────────────────────────────
# The GitHub MCP server exposes 60+ tools. Giving all of them to the LLM causes
# confusion and poor tool selection. We pin an explicit allowlist of the tools
# we actually need. Any tool returned by the server that is not in this set is
# silently dropped before the LLM ever sees it.
#
# Names are the raw MCP server tool names (no server prefix). Filtering is
# applied per-server in load_tools by checking server_name == "github", so we
# don't need the prefix to identify which tools came from GitHub.
#
# TODO(future): replace this static list with embedding-based tool retrieval —
# embed tool descriptions, retrieve top-k relevant for the user query, expose
# only those to the LLM. The filter would plug in at the same point (after
# load_tools) but the allowlist would be dynamic rather than hard-coded.
CORE_GITHUB_TOOLS: frozenset[str] = frozenset(
    [
        # Reading & Discovery
        "get_file_contents",
        "search_repositories",
        "search_code",
        # "search_issues",
        # "list_issues",
        # "issue_read",
        "list_pull_requests",
        "pull_request_read",
        "get_me",
        "list_commits",
        "get_commit",

        # Core Write Operations
        # "create_or_update_file",
        # "push_files",
        # "create_branch",
        # "create_pull_request",
        # "add_issue_comment",
        # "issue_write",
        # "merge_pull_request",
        # "update_pull_request",

        # Releases & Tags
        # "get_latest_release",
        # "list_releases",
    ]
)


def build_mcp_client(
    servers: dict[str, McpServerSpec],
    *,
    auth_token: str,
) -> MultiServerMCPClient:
    """
    Configure the client for the given server set, injecting the right
    bearer token *per server*.

    ─── Learning checkpoint #13: per-server auth ─────────────────────────────

    MCP doesn't standardize auth — each server picks its own model. This
    function bridges that gap by letting each `McpServerSpec` carry an
    optional `static_token`. Two cases:

      1. No `static_token` (default — used by rag/notes).
         The per-request `auth_token` flows through. That token resolves
         to {user_id, org_id} on the server side and Qdrant scopes
         retrieval by org (CLAUDE.md C1). End-to-end user identity.

      2. `static_token` set (used by github).
         The static token is a *service credential* (a GitHub PAT). The
         agent acts under one configured account regardless of who the
         user is. The user's identity is not propagated — that's correct,
         because GitHub has no notion of our internal user/org mapping.

    Why we strip `static_token` before passing each spec on:
        `langchain_mcp_adapters.sessions.create_session` does
        `params = {k: v for k, v in connection.items() if k != "transport"}`
        and splats `**params` into the session creator. Any unknown key
        becomes a kwarg and crashes. `static_token` is *our* internal
        field, not part of the adapter's Connection union.

    Headers are baked into MultiServerMCPClient at construction in the
    0.2.x adapter, so per-request auth → per-request client. Client
    construction is cheap (no network I/O until the first tool call) so
    we don't bother caching.

    # NOTE(future): for production multi-tenant deployments, the static
    # token shouldn't be a single deployment-wide PAT. It should be a
    # per-user OAuth token resolved from a token vault. The shape here
    # already supports that — production callers can construct
    # `mcp_servers` per-request with the right `static_token` for the
    # current user — but we don't ship a token vault.
    """
    out: dict[str, dict] = {}
    for name, spec in servers.items():
        # Pick the bearer: static credential wins; otherwise the per-request
        # user token. Empty string would produce a malformed header, so treat
        # falsy as "not set".
        using_static = bool(spec.get("static_token"))
        token = spec.get("static_token") or auth_token
        token_kind = "static" if using_static else "user"

        # Strip static_token before passing to MultiServerMCPClient — the
        # adapter splats connection dict keys as kwargs into the session
        # creator and would crash on an unknown field.
        connection = {k: v for k, v in spec.items() if k != "static_token"}
        connection["headers"] = {"Authorization": f"Bearer {token}"}
        out[name] = connection

        log.debug(
            "MCP server configured: name=%s url=%s transport=%s token=%s",
            name,
            spec.get("url", "<unknown>"),
            spec.get("transport", "sse"),
            token_kind,
        )

    log.info(
        "Building MCP client for %d server(s): %s",
        len(out),
        ", ".join(out.keys()) if out else "<none>",
    )
    # tool_name_prefix defaults to False — tools keep their original names as
    # defined by the MCP server (e.g. get_me, get_file_contents, docs_search).
    # GitHub tools are identified at load time by server name (see load_tools)
    # rather than by name prefix, so the allowlist filter still works correctly.
    return MultiServerMCPClient(out)


async def load_tools(client: MultiServerMCPClient) -> list[BaseTool]:
    """Aggregate every server's tool list into one flat list.

    GitHub tools are filtered to CORE_GITHUB_TOOLS. All tools from other
    servers pass through unfiltered. This keeps the LLM's tool list focused
    and avoids the tool-explosion problem described in CLAUDE.md C2a.

    Tools are loaded per-server concurrently so we can apply the GitHub
    allowlist filter by server name (not by tool name prefix).
    """
    GITHUB_SERVER = "github"

    async def _load_server(name: str) -> list[BaseTool]:
        tools = await client.get_tools(server_name=name)
        if name == GITHUB_SERVER:
            before = len(tools)
            tools = [t for t in tools if t.name in CORE_GITHUB_TOOLS]
            dropped = before - len(tools)
            if dropped:
                log.info("Dropped %d GitHub tools not in allowlist.", dropped)
        return tools

    try:
        results = await asyncio.gather(
            *[_load_server(name) for name in client.connections]
        )
    except Exception as exc:
        urls = [cfg.get("url", "<unknown>") for cfg in client.connections.values()]
        log.error(
            "Failed to load MCP tools from %s: %s",
            ", ".join(urls) if urls else "<no servers>",
            exc,
            exc_info=True,
        )
        raise

    filtered: list[BaseTool] = [t for server_tools in results for t in server_tools]

    if not filtered:
        log.warning("MCP client returned zero tools — agent will run toolless.")
    else:
        log.info(
            "Loaded %d MCP tools: %s",
            len(filtered),
            ", ".join(t.name for t in filtered),
        )
        for tool in filtered:
            log.debug("  tool available: %s — %s", tool.name, (tool.description or "").splitlines()[0][:120])
    return filtered
