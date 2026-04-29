"""
Compiled tool list — the single seam that produces the final list of
tools the agent binds to.

Two sources feed in:

    1. MCP servers (loaded over SSE / Streamable HTTP via
       `langchain-mcp-adapters` — see agent/tools.py).
    2. The local registry (BaseTool instances declared in Python and
       added via `agent.registry.register` — see agent/registry.py).

Why this lives in its own module rather than inline in core.py:

  - Tool composition has its own concerns (loading, error mapping,
    aggregation, future ranking) that are independent of the streaming
    loop. Pulling them out keeps `run_agent` focused on event flow.
  - It defines a single, obvious place to plug in the tool-finder layer
    (CLAUDE.md C2a — embedding-based or LLM-based tool retrieval). The
    seam is marked below; nothing else changes when that lands.
  - It's testable in isolation — give it a server dict and a registry,
    assert on the returned list — without spinning up the whole agent.

Failure modes (mapped to user-facing reasons):

  - No MCP servers configured AND no local tools registered: the agent
    runs toolless and the no-tool prompt explains why.
  - MCP servers configured but unreachable / handshake failed: we keep
    any local tools, log the MCP error, and (only if the result is
    completely empty) surface a reason the LLM can pass through to the
    user. A traceback is never propagated up — it would crash the
    streaming loop instead of letting the model speak.
"""
from __future__ import annotations

import logging

from langchain_core.tools import BaseTool

from agent.config import McpServerSpec
from agent.registry import registered_tools
from agent.tools import build_mcp_client, load_tools

log = logging.getLogger(__name__)


async def compile_tools(
    *,
    mcp_servers: dict[str, McpServerSpec],
    auth_token: str,
) -> tuple[list[BaseTool], str | None]:
    """
    Build the final tool list passed to the agent.

    Args:
        mcp_servers: Server dict (possibly empty) used to spin up an
            `MultiServerMCPClient` and pull remote tools. Empty dict is
            valid — registry-only deployments are supported.
        auth_token: Bearer token forwarded to MCP servers. Opaque to
            this layer; servers resolve it to {user_id, org_id}.

    Returns:
        `(tools, reason)` — `tools` is the merged list of MCP + registry
        tools (possibly empty). `reason` is None on success; otherwise a
        short, human-readable string the caller passes into the no-tool
        system prompt so the LLM can explain the situation.

    Errors are caught and turned into reasons rather than re-raised. The
    underlying exception is logged with traceback at ERROR level so the
    full detail is recoverable.
    """
    log.info("compile_tools: %d MCP server(s) configured", len(mcp_servers))

    mcp_tools: list[BaseTool] = []
    mcp_error: str | None = None

    if mcp_servers:
        client = build_mcp_client(mcp_servers, auth_token=auth_token)
        try:
            mcp_tools = await load_tools(client)
        except Exception as exc:
            # load_tools already logs the offending URL with traceback.
            # We just translate the failure into a model-facing reason.
            log.error("MCP tool load failed; falling back to registry-only: %s", exc)
            mcp_error = (
                "The tool servers configured for this session could not be reached "
                "and no MCP tools are available. There may be a connectivity or "
                "configuration issue. Let the user know so they can investigate."
            )
    else:
        log.warning(
            "No MCP servers configured. Set RAG_MCP_URL / NOTES_MCP_URL in .env "
            "or pass mcp_servers= to run_agent(). Continuing with registry tools only."
        )

    local_tools = registered_tools()
    tools: list[BaseTool] = [*mcp_tools, *local_tools]

    # ─── Tool-finder seam (CLAUDE.md C2a — TODO future) ───────────────────
    # When tool retrieval lands, narrow `tools` here based on the user's
    # query. The shape stays `list[BaseTool] -> list[BaseTool]`, so no
    # caller has to change. Sketch:
    #
    #     if query is not None and len(tools) > MAX_TOOLS:
    #         tools = await tool_finder.rank(tools, query, top_k=MAX_TOOLS)
    #
    # Until then, the LLM sees the full merged catalog.
    # ──────────────────────────────────────────────────────────────────────

    if not tools:
        # Pick the most informative reason. If MCP failed, that's the
        # interesting fact; otherwise it's just an unconfigured deployment.
        reason = mcp_error or "No tools are connected to this agent."
        log.warning("No tools available: %s", reason)
        return [], reason

    log.info(
        "Compiled tool list: %d MCP + %d registry = %d total",
        len(mcp_tools),
        len(local_tools),
        len(tools),
    )
    return tools, None
