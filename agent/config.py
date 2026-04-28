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

    NOT owned: anything per-request. The user's bearer token (which
    identifies the *caller* to user-aware servers like our RAG/notes
    backends) is a per-request value passed to `run_agent()` — production
    callers forward the user's `Authorization` header through; the CLI
    reads `AGENT_AUTH_TOKEN` from env on its own (see agent/main.py).

    Static service credentials (e.g. a GitHub PAT used by the GitHub MCP
    server) ARE owned here — they're deployment-level, not per-request.
    They're carried on the McpServerSpec via `static_token`.
"""
from __future__ import annotations

from typing import TypedDict

from pydantic_settings import BaseSettings, SettingsConfigDict


class McpServerSpec(TypedDict, total=False):
    """
    Minimal shape passed to `build_mcp_client`. `total=False` because some
    fields are per-server-conditional (e.g. only HTTP transports take a URL,
    only servers with a service credential carry `static_token`).

    Auth model:
        Each MCP server picks its own auth strategy — there is no MCP-level
        standard. We support the two patterns this project actually needs:

        1. Per-request user token (default). When `static_token` is absent,
           `build_mcp_client` injects the bearer token passed to
           `run_agent()`. This is how rag/notes work: the token resolves to
           {user_id, org_id} on the server side and Qdrant scopes by org.

        2. Static service credential. When `static_token` is set, *that*
           token is used as the bearer for this server, regardless of who
           the user is. This is how third-party servers like GitHub MCP
           work: they expect a service credential (a PAT) that the agent
           holds in env, not a user identity token. The user's identity is
           irrelevant to GitHub — the agent acts under one configured
           service account.

        `static_token` is stripped from the spec inside build_mcp_client
        before the dict reaches `MultiServerMCPClient`, since the adapter
        splats unknown keys as kwargs to the session creator and would
        crash on it. See agent/tools.py.
    """
    url: str
    transport: str  # "sse" | "streamable_http"
    static_token: str  # static service credential; stripped before adapter sees it


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── LLM provider + model (C4 — swap via env var only) ─────────────────
    llm_provider: str = "groq"                   # groq | anthropic | ollama | openai
    llm_model: str = "llama-3.3-70b-versatile"

    # Per-provider credentials. Only one needs to be set — `agent/llm.py`
    # picks the one matching `llm_provider`.
    groq_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # OpenAI + any OpenAI-compatible provider (Together AI, Fireworks, LM Studio, …).
    # Leave OPENAI_BASE_URL unset to hit the real OpenAI API; point it at any
    # compatible endpoint to switch providers with zero code changes.
    openai_api_key: str | None = None
    openai_base_url: str | None = None   # None → langchain_openai defaults to api.openai.com

    # ── MCP endpoints (C2b — multi-server) ─────────────────────────────────
    # Defaults for the demo. Production deployments override either by
    # setting their own env vars OR by passing `mcp_servers=` directly to
    # `run_agent()` (see core.py). This is the only place names like "rag"
    # / "notes" / "github" appear — everywhere else operates on a generic
    # dict.
    rag_mcp_url: str | None = None
    notes_mcp_url: str | None = None

    # ── GitHub MCP (https://github.com/github/github-mcp-server) ───────────
    # Hosted endpoint provided by GitHub. Uses Streamable HTTP transport
    # (the spec's newer replacement for SSE) and a GitHub PAT as bearer.
    # The PAT is a *service credential* — the same token authenticates
    # every user's request. This is fundamentally different from rag/notes,
    # where the bearer carries the *user's* identity. See McpServerSpec
    # docstring for the auth-model split this introduces.
    github_mcp_url: str = "https://api.githubcopilot.com/mcp/"
    github_pat: str | None = None

    # ── LangChain Docs MCP (https://docs.langchain.com/use-these-docs) ──────
    # Public hosted server — no auth, Streamable HTTP transport. Provides
    # real-time search over LangChain, LangGraph, and LangSmith docs. Useful
    # when the agent is answering questions about the frameworks this project
    # is built on. Included in the default set whenever the URL is non-empty;
    # remove or blank the env var to exclude it from the tool catalog.
    langchain_docs_mcp_url: str | None = None

    # ── Extended thinking (Anthropic only) ────────────────────────────────
    # Token budget for internal reasoning when enable_thinking=True is sent
    # per-request. Only applies when LLM_PROVIDER=anthropic. Anthropic
    # requires temperature=1 and max_tokens >= budget when thinking is on;
    # agent/llm.py enforces both constraints automatically.
    thinking_budget_tokens: int = 10000

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
    mcp_servers: dict[str, McpServerSpec] = {}

    if settings.rag_mcp_url:
        mcp_servers["rag"] = {"url": settings.rag_mcp_url, "transport": "sse"}

    if settings.notes_mcp_url:
        mcp_servers["notes"] = {"url": settings.notes_mcp_url, "transport": "sse"}

    # GitHub only joins the set when a PAT is configured — without one the
    # server would reject every call, so we'd rather omit it entirely than
    # surface auth failures inside the agent loop.
    if settings.github_pat:
        mcp_servers["github"] = {
            "url": settings.github_mcp_url,
            "transport": "streamable_http",
            "static_token": settings.github_pat,
        }

    # LangChain Docs: public, no auth. Included whenever the URL is set.
    # No static_token needed — build_mcp_client will inject the user bearer
    # by default, but the server ignores any Authorization header it receives.
    if settings.langchain_docs_mcp_url:
        mcp_servers["langchain_docs"] = {
            "url": settings.langchain_docs_mcp_url,
            "transport": "streamable_http",
        }

    return mcp_servers
