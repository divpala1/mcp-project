# NOTES — learning log

A running log of architectural checkpoints and the reasoning behind each
decision. Updated as stages land. Items tagged with the CLAUDE.md numbering
(C1–C6) or the "Key Learning Checkpoints" list at the bottom of CLAUDE.md.

---

## Stage 1 — Foundation (2026-04-23)

### What landed

- `pyproject.toml` — PEP 621 project metadata + direct dependencies.
- `.env.example` — documented env var shape.
- `.env` — local-only copy with dev defaults (API keys blank).
- `docker-compose.yml` — single-service Qdrant at `localhost:6333`.
- `.gitignore` — ignores secrets, venv, old `_archive/` code.
- The old `mcp_server/` directory was moved to `_archive/mcp_server_old/`
  so we can start clean without losing it.

### Decisions worth remembering

**Python version.** The venv is now Python 3.11.15 (upgraded after Stage 1
was initially drafted against 3.10). `pyproject.toml` pins
`requires-python = ">=3.11"` to match CLAUDE.md. Deps were reinstalled
into the fresh venv via `pip install -e ".[observability]"`. We still
use `from __future__ import annotations` everywhere — forward-compat
with 3.12's lazy-annotation rules and consistent style across the repo.

**One process, two faces (FastAPI + FastMCP).** The RAG MCP server will
be a single `uvicorn` process that mounts both a REST app (`/api/*`) and
the MCP SSE transport (`/mcp/sse`). They share the same Qdrant client and
embedding model. Why: debuggability. You can `curl /api/corpus/stats`
while the agent is running to see the same state the MCP tools see.

**Qdrant in Docker, not embedded.** Learning goal: match the shape of a
real deployment. The embedded `QdrantClient(":memory:")` diverges subtly
from the server (persistence, gRPC, concurrency). Running the real server
also gives us the Qdrant dashboard at `http://localhost:6333/dashboard`,
which is gold when debugging org-filter questions later.

**Static bearer-token map for auth (C1).** The MCP spec's real answer is
OAuth 2.1, but that's a rabbit hole. For now: `AUTH_TOKENS_JSON` is a
JSON map of token → `{user_id, org_id}`. A FastAPI dependency validates
the bearer token, resolves identity, and stashes it in a `ContextVar`
that the MCP tool implementations read without changing their signatures.
This gets us real multi-tenant behaviour in ~40 lines — and the
`# TODO(future): OAuth 2.1` comment marks where the production story
slots in.

### Open threads / things to revisit

- [x] Python version upgrade (done: 3.11.15).
- [x] `GROQ_API_KEY` populated in `.env` (done).

---

## Stage 2 — RAG MCP Server (2026-04-23)

### What landed

- `mcp_server/core/config.py` — pydantic-settings; validates
  `AUTH_TOKENS_JSON` at startup (fail-fast on malformed JSON).
- `mcp_server/core/embeddings.py` — singleton sentence-transformers;
  exposes `get_embedding_dim()` instead of a hardcoded 384 so swapping
  models doesn't land you with a mismatched Qdrant collection.
- `mcp_server/core/chunking.py` — fixed-size word chunker with overlap.
- `mcp_server/core/state.py` — Qdrant-backed RAG core. One chunk → one
  point. Payload `{org_id, document_id, title, chunk_index,
  total_chunks, text}`. Payload indexes on `org_id`, `document_id`,
  `chunk_index` for O(log n) filtering.
- `mcp_server/auth.py` — bearer-token middleware + `ContextVar` identity;
  `/api/health` is the only unauthenticated path.
- `mcp_server/server.py` — FastAPI + FastMCP, lifespan event creates the
  collection at startup, five `docs_*` tools, parallel REST surface for
  curl-based debugging.

### Decisions worth remembering

**`chunk_index == 0` as the "document header".** When we need to list
documents (not chunks) we filter on `chunk_index == 0`. That way `docs_list`
touches one point per document instead of scanning every chunk. A tidier
alternative would be a second collection of document-level points, but
for a learning project the chunk-index trick keeps the schema flat.

**State functions are sync; wrappers are async.** `state.py` is pure
sync logic — no asyncio, no HTTP, trivially unit-testable. The MCP tool
wrappers and REST handlers are async and call state via `asyncio.to_thread`.
`ContextVar` auto-propagates across `to_thread`, so identity travels
along if we ever need it deeper in the stack; for clarity we pass
`org_id` as an explicit argument instead.

**Response-size caps per-tool, not generic.** Each tool has its own
truncation policy shaped to its return type:
- `docs_search` truncates each chunk's `text` to 500 chars + `text_truncated` flag.
- `docs_list` caps `limit` at 100 and titles at 200 chars.
- `docs_get` caps the whole serialised response at 8 KB; over cap → returns
  metadata + a preview + `truncated: true` + a hint pointing to `docs_search`.
- `docs_ingest` and `docs_stats` return small payloads; no cap.
A generic "serialize and truncate" helper would be cleaner but useless —
the agent wants *useful* truncation, not a "too big" envelope.

**Structured errors, not exceptions.** `state.get_document` raises
`ValueError` when nothing is found; the tool wrapper catches and returns
`{"error": "not_found", "message": ...}` so the agent *sees* the error
and can adapt, per CLAUDE.md's explicit direction.

### Learning checkpoints surfaced

- #2 (auth as transport concern) — in `auth.py` docstring.
- C1 (tenant isolation) — `_org_filter` is the single chokepoint.
- C5 (huge-data patterns) — per-tool caps; `describe_corpus` is
  metadata-first; `docs_list` paginates via Qdrant scroll offsets.
- C2a (tool namespacing) — every tool is prefixed `docs_`.

### Smoke-test evidence (2026-04-23)

Twelve-step curl battery against `:8000`:
- `401` on missing / invalid bearer token.
- Alice ingests a quantum-computing doc; Bob ingests a widgets doc.
- Alice's `docs_search("qubit")` → her doc only, score 0.57.
- Bob's `docs_search("qubit")` → his widget doc only, score 0.29 (low
  score is the correct signal — org filter hides Alice's doc completely).
- Bob `GET /api/documents/{alice_doc_id}` → `not_found` (filter
  prevents cross-org enumeration).
- Stats: each org sees `total_documents: 1`, `total_chunks: 1`.

## Stage 3 — Notes MCP Server (2026-04-23)

### What landed

- `notes_server/server.py` — a single ~150-line file containing config,
  auth, in-memory storage, two MCP tools (`notes_create`, `notes_list`),
  and a parallel REST surface. Runs on `:8001`.

### Decisions worth remembering

**Duplicated auth, not imported.** `notes_server/server.py` reimplements
the bearer-token / `ContextVar` / `auth_middleware` pattern instead of
importing `mcp_server.auth`. Rationale: each MCP server should be
deployable independently — importing would couple their deployment
lifecycles and dependency surfaces. ~40 lines of duplication is the
honest price. A project with ≥3 MCP servers would extract a shared
`mcp_common` package instead; at 2, it's premature abstraction.

**Same AUTH_TOKENS_JSON across servers.** Both servers read from the
same `.env` entry. This is the right shape: auth is a transport pattern
you reuse across the deployment. The agent holds one bearer token and
it works everywhere.

**In-memory, process-local storage.** The notes dict is wiped on restart.
Flagged in-code so the pattern doesn't tempt future-me into treating it
as a real notes service.

**Most-recent-first ordering.** Reverse insertion order is the friendlier
default for an LLM summarising "what have I done recently." Insertion
order would rarely be what the agent wants.

### Learning checkpoints surfaced

- **#7 (multi-server aggregation, C2b).** Tools have distinct prefixes:
  RAG uses `docs_*`, notes uses `notes_*`. When `MultiServerMCPClient`
  merges both tool lists in Stage 4, there's nothing to disambiguate.

### Smoke-test evidence (2026-04-23)

Six-step curl battery against `:8001`:
- `401` on missing bearer.
- Alice creates two notes; Bob creates one.
- Alice lists → her two notes, most-recent first, Bob's invisible.
- Bob lists → his one note only.

## Stage 4 — Agent (not yet started)

Pending. Covers:
- `get_llm()` factory reading env vars (C4)
- MCP session lifecycle (learning checkpoint #1)
- `create_react_agent` wired with streaming (checkpoints #5, #6)
- LangSmith hook (checkpoint: observability)

## Stage 5 — End-to-end smoke test (not yet started)

The scenario from CLAUDE.md's "How to Run" target state.
