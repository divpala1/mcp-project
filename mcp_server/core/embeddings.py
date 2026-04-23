"""
Sentence-transformers wrapper.

Singleton pattern: the model is loaded once on first use and reused.
First call is slow (~1-2s to load from disk / download on first run);
subsequent calls are cheap.

Default model: all-MiniLM-L6-v2
    - 384-dim embeddings
    - ~22M params, small CPU footprint
    - No API key, no network after first download
    - Good general-purpose baseline for retrieval

Thread-safe via a lock because `embed()` may be called concurrently
from `asyncio.to_thread` — two requests arriving before the first has
finished loading the model would otherwise race to instantiate it.
"""
from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from mcp_server.core.config import settings

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

log = logging.getLogger(__name__)

_model: "SentenceTransformer | None" = None
_lock = threading.Lock()


def _get_model() -> "SentenceTransformer":
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is None:  # double-checked locking
            from sentence_transformers import SentenceTransformer
            log.info("Loading embedding model: %s", settings.embedding_model)
            _model = SentenceTransformer(settings.embedding_model)
    return _model


def get_embedding_dim() -> int:
    """
    Returns the embedding vector's dimension.

    Used by state.ensure_collection() — the Qdrant collection's vector size
    is fixed at creation and must match this. Hardcoding 384 would be a
    footgun the day someone swaps EMBEDDING_MODEL.
    """
    return _get_model().get_embedding_dimension()


def embed(texts: list[str]) -> list[list[float]]:
    """Return one 384-dim vector per input text."""
    vectors = _get_model().encode(texts, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
