"""
Client-side (agent) config via pydantic-settings.

Mirrors the pattern in `mcp_server/core/config.py` — one class, validated
at import, typed everywhere else. The *agent* has a larger surface than
the server (LLM provider choice, multiple MCP endpoints, observability)
so this file is a little fuller.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    rag_mcp_url: str = "http://127.0.0.1:8000/mcp/sse"
    notes_mcp_url: str = "http://127.0.0.1:8001/mcp/sse"

    # Bearer token the agent sends to every MCP server. Must be a key in
    # the server's AUTH_TOKENS_JSON. Same token works for both servers —
    # that's the point of C1: auth is a transport-layer pattern, shared.
    agent_auth_token: str = "tok_alice"

    # ── Observability (optional — safe defaults) ───────────────────────────
    langsmith_api_key: str | None = None
    langsmith_project: str = "mcp-agent-learning"


settings = AgentConfig()
