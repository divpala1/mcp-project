"""
Fixed-size word-based chunker with overlap.

Why chunk at all?
    C5 — huge-data pattern. We never pass full documents to the LLM.
    Chunking is the prerequisite for retrieval: embed chunks, search
    chunks, return chunks. The agent only ever sees retrieved slices.

Why fixed-size over semantic?
    Simplicity. Semantic chunking (sentence-aware, paragraph-aware,
    or embedding-similarity-based) gives better retrieval quality but
    adds dependencies and a teaching diversion. The pattern is the
    same either way — this is the minimum viable version.
    TODO(future): swap in LangChain's SemanticChunker or a sentence
    splitter + token-count merger.

Why word-based over character-based?
    Word counts track loosely with token counts across English text,
    so chunk sizes stay roughly consistent regardless of input shape.
    Characters would let a single URL or long word blow a chunk.
"""
from __future__ import annotations


def chunk_text(
    text: str,
    chunk_size: int = 500,   # words per chunk
    overlap: int = 50,       # words shared between adjacent chunks
) -> list[str]:
    """
    Split text into overlapping word-level chunks.

    Overlap preserves context across chunk boundaries: a sentence that
    starts at the end of chunk N and finishes in chunk N+1 is visible
    in both, so retrieval doesn't miss it.
    """
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap  # slide window back by overlap
    return chunks
