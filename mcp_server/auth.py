"""
Bearer-token auth for the MCP server.

── Learning checkpoint #2: auth is a transport-layer concern ─────────────────
MCP itself has no concept of users — the spec is silent on identity. The
production answer is OAuth 2.1 (draft 2025-06-18 of the MCP spec). Dev mode
uses a static {token → identity} map:

    1. Agent sends `Authorization: Bearer <token>` on every HTTP request
       (both the initial SSE GET and every subsequent POST to /mcp/messages/).
    2. `AuthMiddleware` validates the token and resolves {user_id, org_id}.
    3. Identity is stashed in a `ContextVar` for the duration of the request.
    4. Tool implementations call `require_identity()` to read it — no changes
       to their signatures, no plumbing `Request` through every function.

Why `ContextVar`?
    - Per-asyncio-task, thread-safe, automatically propagated.
    - asyncio.to_thread preserves ContextVars, so sync state.py functions
      invoked from async tool wrappers still see the caller identity if
      they ever need it (we currently pass org_id explicitly for clarity).

Why a pure ASGI middleware class (not BaseHTTPMiddleware)?
    Starlette's BaseHTTPMiddleware buffers the response body, which breaks
    SSE streaming. The MCP SSE endpoint keeps an HTTP connection open and
    sends events incrementally — BaseHTTPMiddleware's body iterator gets
    confused and raises an AssertionError on the second http.response.start
    message. A pure ASGI middleware passes scope/receive/send through directly
    without touching the response, so SSE works correctly.

TODO(future): OAuth 2.1 flow — authorisation server, access tokens with
`sub` and `org` claims, JWT verification instead of a dict lookup.
"""
from __future__ import annotations

import contextvars
import logging
from typing import Callable

from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from mcp_server.core.config import settings

log = logging.getLogger(__name__)

# Default None so "no identity" is an explicit state, not a silent default.
current_identity: contextvars.ContextVar[dict[str, str] | None] = (
    contextvars.ContextVar("current_identity", default=None)
)

# Paths exempt from auth:
#   - /api/health: liveness probe, reached by uptime checks.
#   - /docs, /redoc, /openapi.json: FastAPI-generated Swagger/ReDoc UIs
#     and their schema. These are static pages; authenticating *inside*
#     them (via Swagger's Authorize button → bearer token → per-request
#     header) is how the user exercises protected routes.
UNAUTHED_PATHS = {
    "/api/health",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    "/openapi.json",
}


def resolve_token(token: str) -> dict[str, str] | None:
    """Map a bearer token to {user_id, org_id}; None means unknown."""
    return settings.auth_tokens.get(token)


class AuthMiddleware:
    """
    Pure ASGI middleware that validates bearer tokens without buffering responses.

    Registered via app.add_middleware(AuthMiddleware) in server.py. Unlike
    BaseHTTPMiddleware, this class never touches the response — it passes
    scope/receive/send straight through to the next app, which means SSE
    streaming connections work correctly.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            # Passthrough for WebSocket and lifespan events.
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in UNAUTHED_PATHS:
            await self.app(scope, receive, send)
            return

        # Headers in ASGI scope are a list of (name_bytes, value_bytes) tuples.
        headers: dict[bytes, bytes] = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()

        if not auth_header.startswith("Bearer "):
            response = Response("Unauthorized: missing bearer token", status_code=401)
            await response(scope, receive, send)
            return

        token = auth_header.removeprefix("Bearer ")
        identity = resolve_token(token)
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
    """
    Read caller identity from the ContextVar. Call this inside any tool
    or route handler that needs to know who's calling.
    """
    ident = current_identity.get()
    if ident is None:
        # If you hit this, either AuthMiddleware isn't registered or the
        # handler was invoked outside a request (e.g. unit test without
        # setting the ContextVar manually).
        raise RuntimeError(
            "No identity in context — AuthMiddleware missing, or called "
            "outside an HTTP request?"
        )
    return ident
