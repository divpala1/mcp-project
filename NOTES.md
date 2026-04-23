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

- [ ] Drop real `GROQ_API_KEY` into `.env` before Stage 4.

---

## Stage 2 — RAG MCP Server (not yet started)

Pending. Will cover:
- Org-scoped Qdrant state (C1, C5)
- Tool design with pagination + truncation caps (C5)
- Auth middleware wiring (learning checkpoint #2)
- `list_documents`, `get_document`, `search_documents`, `ingest_document`,
  `describe_corpus`

## Stage 3 — Notes MCP Server (not yet started)

Pending. Tiny second server to demonstrate `MultiServerMCPClient`
aggregation and the value of tool namespacing (C2b).

## Stage 4 — Agent (not yet started)

Pending. Covers:
- `get_llm()` factory reading env vars (C4)
- MCP session lifecycle (learning checkpoint #1)
- `create_react_agent` wired with streaming (checkpoints #5, #6)
- LangSmith hook (checkpoint: observability)

## Stage 5 — End-to-end smoke test (not yet started)

The scenario from CLAUDE.md's "How to Run" target state.
