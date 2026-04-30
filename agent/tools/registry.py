"""
Local tool registry — a place to hand-write Python tools and have them
appear in the agent's tool list alongside tools loaded from MCP servers.

Why a registry (not just passing a list to run_agent):
  - Decouples tool definition from agent composition. A module anywhere
    in the codebase can register a tool at import time without touching
    `agent/core.py` or threading the tool down through call sites.
  - Mirrors the MCP pattern from the LLM's perspective: tools are
    discovered, not enumerated by the agent module. Both sources surface
    as a flat `list[BaseTool]` by the time the LLM binds to them.
  - The future tool-finder layer (CLAUDE.md C2a TODO) ranks tools per
    query — having one uniform registry that includes both MCP and
    locally-defined tools means the finder doesn't care where a tool
    came from.

Usage:

    from datetime import datetime, timezone
    from langchain_core.tools import tool
    from agent.tools import register

    @register
    @tool
    def get_current_time() -> str:
        '''Return the current UTC time in ISO-8601.'''
        return datetime.now(timezone.utc).isoformat()

Or programmatically (no decorator), for tools you receive from
elsewhere:

    register(some_basetool)

Names must be unique. Re-registering the same name replaces the prior
entry and logs a warning — likely a bug, but not fatal so a hot-reload
during development doesn't crash the process.

# TODO(future): when tool retrieval lands (CLAUDE.md C2a), this registry
# is the natural place to attach per-tool metadata (tags, embeddings)
# used to rank candidates against the user's query. The public API
# (register / registered_tools) stays stable; internals grow a metadata
# dict alongside `_registry`.
"""
from __future__ import annotations

import logging

from langchain_core.tools import BaseTool

log = logging.getLogger(__name__)

# Module-level dict, keyed by tool name. Tool names are the LLM-facing
# identifier, so name collisions would be ambiguous to the model — we
# enforce uniqueness here rather than letting two tools shadow each
# other silently in the bound tool list.
_registry: dict[str, BaseTool] = {}


def register(tool: BaseTool) -> BaseTool:
    """
    Add a `BaseTool` to the registry.

    Returns the tool unchanged, which lets `register` work as a decorator
    on top of `@tool`-decorated callables (the common case) or as a
    plain function call for tools constructed elsewhere.

    Raises:
        TypeError: if `tool` is not a `BaseTool` (most common cause: a
            bare function passed without first wrapping with `@tool`).
    """
    if not isinstance(tool, BaseTool):
        raise TypeError(
            f"register() expects a langchain_core.tools.BaseTool, got "
            f"{type(tool).__name__}. Wrap a plain function with @tool first."
        )
    if tool.name in _registry:
        log.warning("Tool %r already registered; replacing previous entry.", tool.name)
    _registry[tool.name] = tool
    log.debug("Registered local tool: %s", tool.name)
    return tool


def unregister(name: str) -> None:
    """Remove a tool by name. No-op if it wasn't registered."""
    if _registry.pop(name, None) is not None:
        log.debug("Unregistered local tool: %s", name)
    else:
        log.debug("unregister(%r): not found, no-op", name)


def registered_tools() -> list[BaseTool]:
    """Return all currently-registered tools as a flat list (insertion order)."""
    tools = list(_registry.values())
    log.debug("registered_tools: %d local tool(s)", len(tools))
    return tools


def clear() -> None:
    """Drop every registered tool. Intended for tests; rarely useful in app code."""
    count = len(_registry)
    _registry.clear()
    log.debug("registry cleared: removed %d tool(s)", count)
