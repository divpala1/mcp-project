"""
Qdrant-backed RAG core — the teaching centrepiece of Stage 2.

What this module demonstrates:

  C1 — tenant isolation via payload filter.
      Every read and write passes through `_org_filter(org_id)`. A user from
      org A *physically cannot* see org B's chunks, even if they guess a
      document_id. The filter is declared once (here) and reused everywhere
      — one chokepoint, easy to audit.

  C5 — huge-data patterns.
      * Retrieval, not loading: `search_documents` returns top-k chunks,
        not the whole corpus.
      * Pagination: `list_documents` takes a cursor.
      * Size caps: per-tool response ceilings (500 chars/search chunk,
        8 KB total for get_document). When truncated, responses carry a
        `truncated: true` flag + a hint so the agent can adapt.
      * Metadata-first: `describe_corpus` returns counts only, no content.

Shape of stored points:
      1 Qdrant point per chunk. Vector = chunk embedding. Payload =
      {org_id, document_id, title, chunk_index, total_chunks, text}.
      `chunk_index == 0` marks the "header" chunk — we filter on that when
      listing documents so we touch one point per document instead of all.

Concurrency:
      Every function here is sync. Async wrappers in server.py call them via
      asyncio.to_thread. Keeping this module sync makes it trivially testable
      without any HTTP or asyncio context.
"""
from __future__ import annotations

import json
import logging
import threading
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from mcp_server.core import embeddings
from mcp_server.core.chunking import chunk_text
from mcp_server.core.config import settings

log = logging.getLogger(__name__)

_client: QdrantClient | None = None
_client_lock = threading.Lock()


def _qc() -> QdrantClient:
    """Lazy singleton Qdrant client. Threadsafe — may be called from to_thread."""
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is None:
            _client = QdrantClient(url=settings.qdrant_url)
    return _client


# ── Collection bootstrap ──────────────────────────────────────────────────────

def ensure_collection() -> None:
    """
    Create the collection + payload indexes if missing. Idempotent.
    Called once at FastAPI startup via the lifespan event.
    """
    c = _qc()
    if c.collection_exists(settings.qdrant_collection):
        return

    log.info("Creating Qdrant collection %r", settings.qdrant_collection)
    c.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(
            size=embeddings.get_embedding_dim(),
            # COSINE is the standard for sentence-transformers embeddings,
            # which are L2-normalised. DOT works on normalised vectors too
            # but COSINE is explicit about intent.
            distance=Distance.COSINE,
        ),
    )
    # Payload indexes speed up filtered queries. For a dev corpus the perf
    # difference is invisible; for production it's the difference between
    # O(log n) and O(n) per query. Declaring them is best practice.
    c.create_payload_index(
        settings.qdrant_collection, field_name="org_id", field_schema="keyword",
    )
    c.create_payload_index(
        settings.qdrant_collection, field_name="document_id", field_schema="keyword",
    )
    c.create_payload_index(
        settings.qdrant_collection, field_name="chunk_index", field_schema="integer",
    )


# ── Filter helpers — the single chokepoint for tenant isolation (C1) ──────────

def _org_filter(org_id: str) -> Filter:
    return Filter(must=[
        FieldCondition(key="org_id", match=MatchValue(value=org_id)),
    ])


def _org_headers_filter(org_id: str) -> Filter:
    """Match only chunk_index==0 points — one per document."""
    return Filter(must=[
        FieldCondition(key="org_id", match=MatchValue(value=org_id)),
        FieldCondition(key="chunk_index", match=MatchValue(value=0)),
    ])


# ── Write: ingest ─────────────────────────────────────────────────────────────

def ingest_document(title: str, content: str, org_id: str) -> dict:
    """Chunk, embed, upsert. Returns the new document_id and chunk count."""
    chunks = chunk_text(content)
    if not chunks:
        return {"status": "empty", "reason": "content had no words"}

    document_id = str(uuid4())
    vectors = embeddings.embed(chunks)
    points = [
        PointStruct(
            id=str(uuid4()),
            vector=vec,
            payload={
                "org_id": org_id,
                "document_id": document_id,
                "title": title,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "text": chunk,
            },
        )
        for i, (chunk, vec) in enumerate(zip(chunks, vectors))
    ]
    # wait=True → return only after the write is durable. Simpler mental
    # model for a learning project; the throughput cost is negligible here.
    _qc().upsert(
        collection_name=settings.qdrant_collection, points=points, wait=True,
    )
    
    # Q: What does 'wait=True' do in the upsert method?
    # A: The 'wait=True' parameter in the upsert method ensures that the method call will block and only return after the write operation is durable. This means that the data has been successfully written to the database and is safe to read. In the context of this code, it simplifies the mental model for a learning project, as it guarantees that once the method returns, the new document and its chunks are fully stored and can be retrieved without any risk of reading stale data. The throughput cost of using 'wait=True' is negligible in this case, as the operations are likely to be fast and the consistency guarantees it provides are more valuable for the intended use case.
    
    return {
        "status": "success",
        "document_id": document_id,
        "title": title,
        "chunks_created": len(chunks),
    }


# ── Read: search ──────────────────────────────────────────────────────────────

_SEARCH_TEXT_CAP = 500   # chars per chunk in search results (C5)
_SEARCH_TOP_K_CAP = 20   # hard upper bound on top_k


def search_documents(query: str, org_id: str, top_k: int = 5) -> list[dict]:
    """
    Embed the query, search the org's chunks, return top-k.
    Each chunk's `text` is truncated to 500 chars; `text_truncated` flags
    when that happened — the agent can call `docs_get` for the full chunk.
    """
    top_k = max(1, min(int(top_k), _SEARCH_TOP_K_CAP))
    qv = embeddings.embed_one(query)
    results = _qc().query_points(
        collection_name=settings.qdrant_collection,
        query=qv,
        query_filter=_org_filter(org_id),
        limit=top_k,
        with_payload=True,
    ).points

    out: list[dict] = []
    for p in results:
        payload = p.payload or {}
        text = payload.get("text", "")
        truncated = len(text) > _SEARCH_TEXT_CAP
        out.append({
            "score": round(p.score, 4),
            "text": text[:_SEARCH_TEXT_CAP] + ("…" if truncated else ""),
            "text_truncated": truncated,
            "title": payload.get("title"),
            "document_id": payload.get("document_id"),
            "chunk_index": payload.get("chunk_index"),
        })
    return out


# ── Read: list documents (paginated) ──────────────────────────────────────────

_LIST_LIMIT_CAP = 100


def list_documents(
    org_id: str, limit: int = 20, cursor: str | None = None,
) -> dict:
    """
    Paginate through documents for an org — one point per document.

    `cursor` is the Qdrant scroll offset (an opaque point-id string).
    Pass None to start; pass back whatever `next_cursor` returned to page.
    """
    limit = max(1, min(int(limit), _LIST_LIMIT_CAP))
    c = _qc()

    points, next_offset = c.scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=_org_headers_filter(org_id),
        limit=limit,
        offset=cursor,
        with_payload=True,
        with_vectors=False,
    )

    items = [
        {
            "document_id": (p.payload or {}).get("document_id"),
            # Cap title length to avoid a pathological list blowing response size.
            "title": ((p.payload or {}).get("title") or "")[:200],
            "total_chunks": (p.payload or {}).get("total_chunks"),
        }
        for p in points
    ]

    # Cheap exact count — Qdrant maintains counts on indexed fields.
    total = c.count(
        collection_name=settings.qdrant_collection,
        count_filter=_org_headers_filter(org_id),
        exact=True,
    ).count

    return {
        "items": items,
        "next_cursor": str(next_offset) if next_offset is not None else None,
        "total": total,
    }


# ── Read: get full document ───────────────────────────────────────────────────

_GET_RESPONSE_CAP_BYTES = 8 * 1024


def get_document(document_id: str, org_id: str) -> dict:
    """
    Fetch all chunks for a document, concatenated in chunk_index order.

    Scoped to the calling org — guessing another org's document_id returns
    "not found", indistinguishable from a genuinely missing id. This keeps
    tenant isolation airtight even against known-id enumeration.
    """
    doc_filter = Filter(must=[
        FieldCondition(key="org_id", match=MatchValue(value=org_id)),
        FieldCondition(key="document_id", match=MatchValue(value=document_id)),
    ])

    points, _ = _qc().scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=doc_filter,
        limit=1000,  # practical upper bound on chunks per document
        with_payload=True,
        with_vectors=False,
    )
    if not points:
        raise ValueError(f"Document {document_id!r} not found")

    chunks = sorted(
        [p.payload or {} for p in points],
        key=lambda d: d.get("chunk_index", 0),
    )
    title = chunks[0].get("title")
    total = chunks[0].get("total_chunks", len(chunks))
    full_text = "\n\n".join(c.get("text", "") for c in chunks)

    payload: dict = {
        "document_id": document_id,
        "title": title,
        "total_chunks": total,
        "text": full_text,
    }

    # Response-size cap (C5). A 200-page PDF's full text shouldn't flow
    # through the LLM's context — the agent should use docs_search for that.
    encoded_len = len(json.dumps(payload))
    if encoded_len > _GET_RESPONSE_CAP_BYTES:
        preview_chars = _GET_RESPONSE_CAP_BYTES // 2
        payload = {
            "document_id": document_id,
            "title": title,
            "total_chunks": total,
            "text": full_text[:preview_chars] + "…",
            "truncated": True,
            "hint": (
                "document exceeds response cap; use docs_search with a "
                "specific query to retrieve only the relevant chunks"
            ),
            "original_size_bytes": encoded_len,
        }
    return payload


# ── Read: corpus stats (metadata, not content) ────────────────────────────────

def describe_corpus(org_id: str) -> dict:
    """
    C5 — metadata-first tool. An agent calls this to decide what to retrieve;
    it never pulls content through here.
    """
    c = _qc()
    chunk_count = c.count(
        collection_name=settings.qdrant_collection,
        count_filter=_org_filter(org_id),
        exact=True,
    ).count
    doc_count = c.count(
        collection_name=settings.qdrant_collection,
        count_filter=_org_headers_filter(org_id),
        exact=True,
    ).count
    return {
        "org_id": org_id,
        "total_documents": doc_count,
        "total_chunks": chunk_count,
        "embedding_model": settings.embedding_model,
        "collection": settings.qdrant_collection,
    }
