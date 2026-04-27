"""
RAG MCP server — FastAPI + FastMCP in one process.

Why one process?
    Both the REST layer (/api/*) and the MCP SSE transport (/mcp/sse) share
    the same `core.state` module — one Qdrant client, one embedding model.
    The REST endpoints are a debug window into MCP-tool state: you can
    curl them to verify behaviour without spinning up the agent. In a
    production deployment you might split them; here, co-location is a
    feature of the learning setup.

Tool naming:
    Every MCP tool is prefixed `docs_` (C2 — namespacing). This keeps
    collisions out of the picture once the notes MCP server lands in
    Stage 3 and `MultiServerMCPClient` merges both sets of tools.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.security import HTTPBearer
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from mcp_server import auth
from mcp_server.core import state

# Swagger-UI affordance. HTTPBearer declares the scheme on the OpenAPI
# spec so Swagger's "Authorize" button appears and auto-injects the
# header into "Try it out" calls. auto_error=False because actual
# enforcement lives in auth.auth_middleware — this Depends() is purely
# a documentation hook, not a second enforcement layer.
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Bearer token (e.g. tok_alice). Same map as AUTH_TOKENS_JSON in .env.",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger(__name__)


# ── Lifespan: ensure the Qdrant collection exists before serving ─────────────
# FastAPI runs this once at startup. It's the natural place for expensive
# one-time setup — avoids the "first request is slow" problem and makes
# bootstrap failures (Qdrant down, embedding model unavailable) surface
# immediately instead of at request time.
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Ensuring Qdrant collection exists…")
    await asyncio.to_thread(state.ensure_collection)
    log.info("Ready.")
    yield
    # No teardown — QdrantClient holds no persistent resources to close.


app = FastAPI(title="RAG MCP Server", version="0.2.0", lifespan=lifespan)

# Register auth middleware. add_middleware inserts it before the app, so it
# protects both FastAPI routes and the mounted MCP SSE sub-app. We use the
# pure ASGI class (not app.middleware("http")) because BaseHTTPMiddleware
# buffers responses and breaks SSE streaming. See auth.AuthMiddleware for details.
app.add_middleware(auth.AuthMiddleware)


# ── MCP layer ─────────────────────────────────────────────────────────────────
# Thin async wrappers around state.* — pull identity from the ContextVar,
# then delegate to the sync core via asyncio.to_thread. Tools return plain
# dicts/lists; FastMCP handles JSON-RPC framing and schema generation from
# the type hints + docstrings.
mcp = FastMCP("rag-server")


@mcp.tool()
async def docs_ingest(title: str, content: str) -> dict:
    """
    Ingest a document into the calling org's corpus.
    Returns {status, document_id, title, chunks_created}.
    """
    org_id = auth.require_identity()["org_id"]
    return await asyncio.to_thread(state.ingest_document, title, content, org_id)


@mcp.tool()
async def docs_search(query: str, top_k: int = 5) -> dict:
    """
    Search the calling org's corpus for chunks relevant to `query`.
    Returns {results, count}. Each result has {score, text, title, document_id,
    chunk_index}; text is truncated to 500 chars (text_truncated flags this).
    Call docs_get for the full document.
    """
    org_id = auth.require_identity()["org_id"]
    results = await asyncio.to_thread(state.search_documents, query, org_id, top_k)
    # Wrap in a dict so the tool response is never a bare empty list.
    # Groq rejects ToolMessage content=[] ("minimum number of items is 1");
    # a dict is always non-empty at minimum {"results": [], "count": 0}.
    # Same pattern as notes_server.notes_list.
    return {"results": results, "count": len(results)}


@mcp.tool()
async def docs_list(limit: int = 20, cursor: str | None = None) -> dict:
    """
    List documents in the calling org's corpus with pagination.
    Returns {items, next_cursor, total}. Pass next_cursor back to page forward.
    """
    org_id = auth.require_identity()["org_id"]
    return await asyncio.to_thread(state.list_documents, org_id, limit, cursor)


@mcp.tool()
async def docs_get(document_id: str) -> dict:
    """
    Fetch a full document by id. Scoped to the calling org — a document
    belonging to a different org returns 'not found' the same as a bogus id.
    Large documents are truncated (truncated=True) with a hint to use docs_search.
    """
    org_id = auth.require_identity()["org_id"]
    try:
        return await asyncio.to_thread(state.get_document, document_id, org_id)
    except ValueError as e:
        # Structured error so the agent can see + adapt, per CLAUDE.md.
        return {"error": "not_found", "message": str(e)}


@mcp.tool()
async def docs_stats() -> dict:
    """
    Corpus metadata for the calling org: {total_documents, total_chunks,
    embedding_model, collection}. C5 — metadata, not content.
    """
    org_id = auth.require_identity()["org_id"]
    return await asyncio.to_thread(state.describe_corpus, org_id)


# ── REST layer — mirrors the MCP tools for human/curl debugging ──────────────

class IngestBody(BaseModel):
    title: str
    content: str


@app.get("/api/health")
def health() -> dict:
    # Only endpoint exempt from auth (see auth.UNAUTHED_PATHS).
    return {"status": "ok"}


@app.post("/api/ingest", dependencies=[Depends(bearer_scheme)])
async def api_ingest(body: IngestBody) -> dict:
    org_id = auth.require_identity()["org_id"]
    return await asyncio.to_thread(state.ingest_document, body.title, body.content, org_id)


@app.get("/api/search", dependencies=[Depends(bearer_scheme)])
async def api_search(q: str, top_k: int = 5) -> list[dict]:
    org_id = auth.require_identity()["org_id"]
    return await asyncio.to_thread(state.search_documents, q, org_id, top_k)


@app.get("/api/documents", dependencies=[Depends(bearer_scheme)])
async def api_list_documents(limit: int = 20, cursor: str | None = None) -> dict:
    org_id = auth.require_identity()["org_id"]
    return await asyncio.to_thread(state.list_documents, org_id, limit, cursor)


@app.get("/api/documents/{document_id}", dependencies=[Depends(bearer_scheme)])
async def api_get_document(document_id: str) -> dict:
    org_id = auth.require_identity()["org_id"]
    try:
        return await asyncio.to_thread(state.get_document, document_id, org_id)
    except ValueError as e:
        return {"error": "not_found", "message": str(e)}


@app.get("/api/corpus/stats", dependencies=[Depends(bearer_scheme)])
async def api_corpus_stats() -> dict:
    org_id = auth.require_identity()["org_id"]
    return await asyncio.to_thread(state.describe_corpus, org_id)


# ── Mount MCP SSE app at /mcp ─────────────────────────────────────────────────
# After mount, MCP clients connect to:
#     GET  /mcp/sse          event stream (long-lived)
#     POST /mcp/messages/    JSON-RPC requests
# Auth middleware (above) fires on every one of these requests.
app.mount("/mcp", mcp.sse_app())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
