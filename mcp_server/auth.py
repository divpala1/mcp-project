"""
Bearer-token auth for the MCP server.

── Learning checkpoint #2: auth is a transport-layer concern ─────────────────
MCP itself has no concept of users — the spec is silent on identity. The
production answer is OAuth 2.1 (draft 2025-06-18 of the MCP spec). Dev mode
uses a static {token → identity} map:

    1. Agent sends `Authorization: Bearer <token>` on every HTTP request
       (both the initial SSE GET and every subsequent POST to /mcp/messages/).
    2. `auth_middleware` validates the token and resolves {user_id, org_id}.
    3. Identity is stashed in a `ContextVar` for the duration of the request.
    4. Tool implementations call `require_identity()` to read it — no changes
       to their signatures, no plumbing `Request` through every function.

Why `ContextVar`?
    - Per-asyncio-task, thread-safe, automatically propagated.
    - asyncio.to_thread preserves ContextVars, so sync state.py functions
      invoked from async tool wrappers still see the caller identity if
      they ever need it (we currently pass org_id explicitly for clarity).

TODO(future): OAuth 2.1 flow — authorisation server, access tokens with
`sub` and `org` claims, JWT verification instead of a dict lookup.
"""
from __future__ import annotations

import contextvars
import logging

from fastapi import Request
from fastapi.responses import Response

from mcp_server.core.config import settings

log = logging.getLogger(__name__)

# Default None so "no identity" is an explicit state, not a silent default.
current_identity: contextvars.ContextVar[dict[str, str] | None] = (
    contextvars.ContextVar("current_identity", default=None)
)

# Liveness-only endpoint: exempt from auth so uptime checks can reach it.
UNAUTHED_PATHS = {"/api/health"}


def resolve_token(token: str) -> dict[str, str] | None:
    """Map a bearer token to {user_id, org_id}; None means unknown."""
    return settings.auth_tokens.get(token)


async def auth_middleware(request: Request, call_next):
    """
    Runs before every request, including FastAPI routes *and* the mounted
    MCP SSE sub-app — Starlette middleware wraps the whole app.
    """
    if request.url.path in UNAUTHED_PATHS:
        return await call_next(request)

    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return Response("Unauthorized: missing bearer token", status_code=401)

    token = header.removeprefix("Bearer ")
    identity = resolve_token(token)
    if identity is None:
        log.warning("Rejected unknown token (prefix=%s…)", token[:6])
        return Response("Unauthorized: invalid token", status_code=401)

    ctx_tok = current_identity.set(identity)
    try:
        return await call_next(request)
    finally:
        current_identity.reset(ctx_tok)


def require_identity() -> dict[str, str]:
    """
    Read caller identity from the ContextVar. Call this inside any tool
    or route handler that needs to know who's calling.
    """
    ident = current_identity.get()
    if ident is None:
        # If you hit this, either auth_middleware isn't registered or the
        # handler was invoked outside a request (e.g. unit test without
        # setting the ContextVar manually).
        raise RuntimeError(
            "No identity in context — auth_middleware missing, or called "
            "outside an HTTP request?"
        )
    return ident
