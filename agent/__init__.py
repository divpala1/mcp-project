"""
Public API of the agent package.

Hosts (CLI, FastAPI, tests, future production app) consume the agent
through these names. Internal layout (core.py, tools.py, llm.py, etc.)
is not part of the public contract — re-organize freely without
breaking callers.

    from agent import run_agent, AgentEvent, McpServerSpec

For the optional FastAPI router, import explicitly:

    from agent.api import router
"""
from __future__ import annotations

from agent.config import McpServerSpec
from agent.core import AgentEvent, run_agent

__all__ = ["run_agent", "AgentEvent", "McpServerSpec"]
