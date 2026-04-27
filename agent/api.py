"""
Optional FastAPI surface for the agent.

This module is *optional*. Hosts that don't import `agent.api` don't pull
the FastAPI router into their app, so a CLI-only / non-HTTP host pays
nothing for it.

Usage from any FastAPI host:

    from fastapi import FastAPI
    from agent.api import router

    app = FastAPI()
    app.include_router(router)

The host gets `POST /agent/chat` exposing the agent as an SSE-streaming
endpoint that respects the caller's `Authorization` header — see
`agent/app.py` for the minimal demo host, or compose this router into a
larger production FastAPI application.

Why SSE (and not WebSockets / plain JSON):
    - LangGraph's `astream_events` is already an async iterator; SSE is
      the simplest one-way streaming shape that maps onto it directly.
    - Browsers + curl both consume it without ceremony.
    - WebSockets would add bidirectional capability we don't need yet
      (single-turn requests). When per-conversation memory + interactive
      cancellation lands, WS becomes interesting.

What the default router intentionally does NOT expose:
    - `mcp_servers` is not a request body field. The default endpoint
      always uses env defaults. Production hosts that need per-user MCP
      server resolution skip this router and write their own thin
      endpoint that resolves the dict and calls `run_agent(...,
      mcp_servers=...)` directly. Keeps the public API surface secure
      (no caller-supplied URLs) while leaving the override path open at
      the callable level.
    - LLM provider / model overrides — those are deployment decisions.
"""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.core import AgentEvent, run_agent

log = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    prompt: str
    # Per-request opt-in to extended thinking. Only meaningful for
    # LLM_PROVIDER=anthropic — other providers silently ignore it.
    enable_thinking: bool = False


def _extract_bearer(authorization: str | None) -> str:
    """
    Pull the token out of an `Authorization: Bearer <token>` header.

    The agent does not validate the token itself — the MCP server is the
    source of truth on identity (`mcp_server/auth.py` rejects unknown
    tokens on every call). We only check that *something* was provided,
    so we fail fast at the FastAPI layer instead of letting an empty
    header reach MCP.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or malformed Authorization header (expected 'Bearer <token>')",
        )
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token")
    return token


async def _sse_stream(
    prompt: str, auth_token: str, enable_thinking: bool
) -> AsyncIterator[str]:
    """
    Convert AgentEvent dicts into SSE `data:` frames.

    `default=str` on json.dumps shields us from values that aren't
    JSON-serializable out of the box (e.g. ToolMessage objects appearing
    in tool outputs). They get stringified rather than crashing the
    stream — verbose but safe.
    """
    async for ev in run_agent(prompt, auth_token=auth_token, enable_thinking=enable_thinking):
        yield f"data: {json.dumps(ev, default=str)}\n\n"


@router.post("/chat")
async def chat(
    req: ChatRequest,
    authorization: str | None = Header(default=None),
) -> StreamingResponse:
    """
    Run the agent for one turn and stream events over SSE.

    Auth model: the caller's `Authorization: Bearer <token>` header is
    forwarded verbatim to the MCP servers, preserving end-to-end identity.
    Multi-tenant correctness depends on this — Qdrant scopes by org_id
    derived from the token.
    """
    token = _extract_bearer(authorization)
    return StreamingResponse(
        _sse_stream(req.prompt, token, req.enable_thinking),
        media_type="text/event-stream",
        headers={
            # Standard SSE hygiene: prevent buffering at any intermediate
            # proxy (nginx, in particular, holds chunks back without this).
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
