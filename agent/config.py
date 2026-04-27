"""
Client-side (agent) config via pydantic-settings.

Mirrors the pattern in `mcp_server/core/config.py` — one class, validated
at import, typed everywhere else. The *agent* has a larger surface than
the server (LLM provider choice, multiple MCP endpoints, observability)
so this file is a little fuller.

What this file owns vs. what it doesn't:
    Owned: deployment-level facts that don't vary per request (LLM choice,
    credentials, observability). Plus the env-driven *default* MCP server
    list, exposed via `default_mcp_servers()`.

    NOT owned: anything per-request. The bearer token used to authenticate
    against MCP servers is now a per-request value passed to `run_agent()`
    — production callers forward the user's `Authorization` header through;
    the CLI reads `AGENT_AUTH_TOKEN` from env on its own (see agent/main.py).
"""
from __future__ import annotations

from typing import TypedDict

from pydantic_settings import BaseSettings, SettingsConfigDict


class McpServerSpec(TypedDict):
    """Minimal shape passed to `build_mcp_client`. Only fields the agent
    cares about — `headers` are added at client-construction time so they
    can carry the per-request bearer token."""
    url: str
    transport: str  # "sse"


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── LLM provider + model (C4 — swap via env var only) ─────────────────
    llm_provider: str = "groq"                   # groq | anthropic | ollama
    llm_model: str = "llama-3.3-70b-versatile"

    # Per-provider credentials. Only one needs to be set — `agent/llm.py`
    # picks the one matching `llm_provider`.
    groq_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # ── MCP endpoints (C2b — multi-server) ─────────────────────────────────
    # Defaults for the demo. Production deployments override either by
    # setting their own env vars OR by passing `mcp_servers=` directly to
    # `run_agent()` (see core.py). This is the only place names like "rag"
    # / "notes" appear — everywhere else operates on a generic dict.
    rag_mcp_url: str = ""
    notes_mcp_url: str = ""

    # ── Observability (optional — safe defaults) ───────────────────────────
    langsmith_api_key: str | None = None
    langsmith_project: str = "mcp-agent-learning"


settings = AgentConfig()


def default_mcp_servers() -> dict[str, McpServerSpec]:
    """
    Env-driven default MCP server set used when `run_agent()` is called
    without an explicit `mcp_servers` override.

    Why a function (not a module-level constant): keeps the helper
    re-evaluable in tests that monkey-patch `settings`, and avoids
    surprising people who change env between imports.
    """
    mcp_servers = {}

    if settings.rag_mcp_url:
        mcp_servers["rag"] = {"url": settings.rag_mcp_url, "transport": "sse"}

    if settings.notes_mcp_url:
        mcp_servers["notes"] = {"url": settings.notes_mcp_url, "transport": "sse"}

    return mcp_servers
