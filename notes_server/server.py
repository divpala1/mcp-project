"""
Notes MCP server — the tiny second server (Stage 3).

Its sole job: demonstrate that `MultiServerMCPClient` in the agent will
aggregate tools from multiple MCP servers, and that tool namespacing
(here: `notes_*`) keeps names distinct from the RAG server's `docs_*`.

Architectural choices:

  - Self-contained. Config + auth + storage live in this one file.
    The RAG server's `mcp_server/auth.py` is deliberately *not* imported.
    Each MCP server should be deployable independently; the ~40 lines
    of duplicated auth is the price of that independence, and it keeps
    the dependency surface of this server easy to eyeball.

  - In-memory storage. Notes live in a dict keyed by `org_id`, wiped on
    restart. This is a demo server, not a notes service.

  - Shared AUTH_TOKENS_JSON with the RAG server. Auth is a transport
    pattern you naturally reuse across servers in a deployment — any
    authorised agent token works against both. Same ContextVar pattern
    as mcp_server/auth.py so the concept stays consistent across the
    project.

  - Port 8001 (RAG is on 8000). The agent (Stage 4) will connect to both.
"""
from __future__ import annotations

import asyncio
import contextvars
import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI
from fastapi.security import HTTPBearer
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

# Swagger-UI documentation hook — see mcp_server/server.py for full rationale.
# auto_error=False because enforcement is in auth_middleware below.
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Bearer token (e.g. tok_alice). Same map as AUTH_TOKENS_JSON in .env.",
)


# ── Config ────────────────────────────────────────────────────────────────────

class NotesConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Same shape and source as the RAG server's config. Validated at import.
    auth_tokens_json: str = '{"tok_alice":{"user_id":"alice","org_id":"acme"}}'

    @property
    def auth_tokens(self) -> dict[str, dict[str, str]]:
        return json.loads(self.auth_tokens_json)

    @field_validator("auth_tokens_json")
    @classmethod
    def _validate_tokens_json(cls, v: str) -> str:
        try:
            parsed = json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"AUTH_TOKENS_JSON is not valid JSON: {e}") from e
        if not isinstance(parsed, dict):
            raise ValueError("AUTH_TOKENS_JSON must be a JSON object")
        return v


settings = NotesConfig()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger(__name__)


# ── Auth — same shape as mcp_server/auth.py (duplicated, not imported) ───────

current_identity: contextvars.ContextVar[dict[str, str] | None] = (
    contextvars.ContextVar("current_identity", default=None)
)


# Paths exempt from auth — liveness + Swagger/ReDoc pages (static HTML).
# Authentication happens *inside* Swagger via its Authorize button.
_UNAUTHED_PATHS = {
    "/api/health",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    "/openapi.json",
}


class AuthMiddleware:
    """
    Pure ASGI middleware — works correctly with SSE streaming.

    BaseHTTPMiddleware (used by app.middleware("http")) buffers responses, which
    breaks the long-lived SSE connection the MCP client holds open. This class
    passes scope/receive/send through without touching the response body.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in _UNAUTHED_PATHS:
            await self.app(scope, receive, send)
            return

        headers: dict[bytes, bytes] = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()

        if not auth_header.startswith("Bearer "):
            response = Response("Unauthorized: missing bearer token", status_code=401)
            await response(scope, receive, send)
            return

        token = auth_header.removeprefix("Bearer ")
        identity = settings.auth_tokens.get(token)
        if identity is None:
            log.warning("Rejected unknown token (prefix=%s…)", token[:6])
            response = Response("Unauthorized: invalid token", status_code=401)
            await response(scope, receive, send)
            return

        ctx_tok = current_identity.set(identity)
        try:
            await self.app(scope, receive, send)
        finally:
            current_identity.reset(ctx_tok)


def require_identity() -> dict[str, str]:
    ident = current_identity.get()
    if ident is None:
        raise RuntimeError("No identity in context — auth_middleware missing?")
    return ident


# ── Storage — process-local, org-scoped ──────────────────────────────────────
# { org_id: [ {id, text, created_at}, ... ] }
# Wiped on restart. C1 isolation is enforced simply by keying on org_id.
_notes: dict[str, list[dict]] = {}


def _create(org_id: str, text: str) -> dict:
    note = {
        "id": str(uuid4()),
        "text": text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _notes.setdefault(org_id, []).append(note)
    return note


def _list(org_id: str) -> list[dict]:
    # Most-recent-first is the friendlier default for an LLM summarising
    # "what did I do recently" — leaking insertion order is rarely useful.
    return list(reversed(_notes.get(org_id, [])))


# ── App + middleware ─────────────────────────────────────────────────────────

app = FastAPI(title="Notes MCP Server", version="0.1.0")
app.add_middleware(AuthMiddleware)

mcp = FastMCP("notes-server")


# ── MCP tools ────────────────────────────────────────────────────────────────

@mcp.tool()
async def create(text: str) -> dict:
    """
    Create a note in the calling org's workspace.
    Returns {id, text, created_at}.
    """
    org_id = require_identity()["org_id"]
    return await asyncio.to_thread(_create, org_id, text)


@mcp.tool()
async def list() -> dict:  # noqa: A001
    """List the calling org's notes, most recent first. Returns {notes, count}."""
    org_id = require_identity()["org_id"]
    notes = await asyncio.to_thread(_list, org_id)
    # Wrap in a dict so the MCP tool response is never a bare empty list.
    # Groq (and other providers) reject ToolMessage content=[] — a dict is always
    # non-empty at minimum {"notes": [], "count": 0}, which satisfies the constraint.
    return {"notes": notes, "count": len(notes)}


# ── REST surface for debugging ───────────────────────────────────────────────

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


class CreateBody(BaseModel):
    text: str


@app.post("/api/notes", dependencies=[Depends(bearer_scheme)])
async def api_create(body: CreateBody) -> dict:
    org_id = require_identity()["org_id"]
    return await asyncio.to_thread(_create, org_id, body.text)


@app.get("/api/notes", dependencies=[Depends(bearer_scheme)])
async def api_list() -> dict:
    org_id = require_identity()["org_id"]
    notes = await asyncio.to_thread(_list, org_id)
    return {"notes": notes, "count": len(notes)}


# ── Mount MCP SSE at /mcp ────────────────────────────────────────────────────
app.mount("/mcp", mcp.sse_app())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
