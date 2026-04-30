"""
Tool management subpackage.

Three concerns live here:

    mcp.py      — MCP client builder and tool loader (MultiServerMCPClient).
    registry.py — Local Python tool registry (register / registered_tools).
    toolset.py  — Composition layer: merges MCP + registry into the final
                  list the agent binds to. This is the seam for the future
                  tool-finder layer (CLAUDE.md C2a).

Everything a caller typically needs is re-exported here so the import
surface stays flat:

    from agent.tools import compile_tools          # agent/core.py
    from agent.tools import register               # tool authors
    from agent.tools import build_mcp_client       # advanced / testing
"""
from __future__ import annotations

from agent.tools.mcp import CORE_GITHUB_TOOLS, build_mcp_client, load_tools
from agent.tools.registry import clear, register, registered_tools, unregister
from agent.tools.toolset import compile_tools

__all__ = [
    # toolset
    "compile_tools",
    # registry
    "register",
    "unregister",
    "registered_tools",
    "clear",
    # mcp
    "build_mcp_client",
    "load_tools",
    "CORE_GITHUB_TOOLS",
]
