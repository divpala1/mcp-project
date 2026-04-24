# MCP Learning Project

A hands-on learning project for building a production-shaped AI agent that connects to MCP (Model Context Protocol) servers. The agent runs on LangGraph; the MCP servers are FastAPI + FastMCP; retrieval is Qdrant-backed with per-organisation isolation.

The whole project is deliberately small enough to read end-to-end in a sitting, while being structured the way a real engineering team would structure it: explicit state, pluggable LLM provider, observable, multi-tenant-aware, and ready to scale into multi-agent systems.

See [`CLAUDE.md`](CLAUDE.md) for the project's learning goals and design calibration, and [`NOTES.md`](NOTES.md) for a stage-by-stage log of the architectural decisions as the code landed.

---

## What's in here

Three independently-runnable components:

| Component | Role | Port |
|---|---|---|
| **`rag-server`** ([`mcp_server/`](mcp_server/)) | RAG MCP server — ingest, chunk, embed, search documents. Qdrant-backed. Per-org tenant isolation via payload filter. | `8000` |
| **`notes-server`** ([`notes_server/`](notes_server/)) | Tiny second MCP server — create/list personal notes. In-memory. Demonstrates multi-server aggregation and tool namespacing. | `8001` |
| **`agent`** ([`agent/`](agent/)) | LangGraph ReAct agent. Connects to both MCP servers via SSE, aggregates tools, streams tokens. Provider-pluggable (Groq / Anthropic / Ollama) via one env var. | (CLI) |

Supporting infrastructure:

- **Qdrant** — vector DB, runs in Docker via [`docker-compose.yml`](docker-compose.yml).

---

## Features

- **Tenant isolation** — every Qdrant query filters by `org_id`; guessing another org's `document_id` returns "not found". Enforced at a single chokepoint in [`mcp_server/core/state.py`](mcp_server/core/state.py).
- **Bearer-token auth** — transport-layer, `ContextVar`-scoped. Same token works across both MCP servers. Swagger UI "Authorize" button is wired up.
- **Tool namespacing** — `docs_*` on the RAG server, `notes_*` on the notes server. No collisions when `MultiServerMCPClient` merges tool lists.
- **Huge-data patterns** — pagination cursors, per-tool response-size caps, structured truncation with hints.
- **Streaming** — token-by-token output via LangGraph's `astream_events`.
- **Provider-pluggable LLM** — `LLM_PROVIDER=groq|anthropic|ollama` in `.env`, nothing else changes.
- **Observability** — optional LangSmith tracing; silently skipped if `LANGSMITH_API_KEY` is unset.
- **Multi-agent ready** — the agent is a `CompiledStateGraph`, so a future supervisor can embed it as a sub-graph node without a rewrite.

---

## Prerequisites

- **Python 3.11+**
- **Docker** + `docker compose` (for Qdrant)
- **An LLM provider credential** — one of:
  - Groq API key (default; recommended for learning — fast, good tool calling)
  - Anthropic API key
  - A local Ollama install serving a tool-capable model

---

## One-time setup

```bash
# 1. Create the venv
python3.11 -m venv venv
source venv/bin/activate

# 2. Install the project + all deps (editable install)
pip install -e ".[observability]"

# 3. Create your local env file and edit it
cp .env.example .env
# then edit .env to set GROQ_API_KEY (or ANTHROPIC_API_KEY / Ollama host)
```

The project pins its Python packages in [`pyproject.toml`](pyproject.toml). The `observability` extra installs `langsmith`; safe to omit if you don't want tracing.

---

## Running the stack

Open three terminals (one per long-running process). The first two stay up; the third is where you invoke the agent.

### Terminal 1 — Qdrant

```bash
docker compose up
```

Health check: `curl http://localhost:6333/readyz` should return `all shards are ready`.<br>
Dashboard: <http://localhost:6333/dashboard> (useful for inspecting collections).<br>
Add `-d` to run in detached mode.

### Terminal 2 — RAG MCP server

```bash
source venv/bin/activate
uvicorn mcp_server.server:app --host 127.0.0.1 --port 8000
```

The first startup downloads the `all-MiniLM-L6-v2` sentence-transformers model (~90 MB, cached after). Qdrant collection `documents` is created automatically on first startup via the FastAPI lifespan event.

### Terminal 3a — Notes MCP server

```bash
source venv/bin/activate
uvicorn notes_server.server:app --host 127.0.0.1 --port 8001
```

### Terminal 3b — the agent

```bash
source venv/bin/activate
python -m agent.main "Ingest a document titled 'Quantum Computing' with content: Qubit entanglement is foundational to quantum computing. Then search for qubit entanglement. Finally, add a note saying I did this search today."
```

The agent will:
1. Load 7 tools across both MCP servers.
2. Call `docs_ingest` (RAG).
3. Call `docs_search` (RAG).
4. Call `notes_create` (notes).
5. Stream a synthesised final answer token-by-token.

---

## Swagger UI

Both MCP servers expose auto-generated OpenAPI docs for their REST surface (a debug mirror of the MCP tools):

- RAG:   <http://127.0.0.1:8000/docs>
- Notes: <http://127.0.0.1:8001/docs>

**To authenticate:** click the **Authorize** button at the top, paste a bearer token (`tok_alice` or `tok_bob` by default), and "Try it out" on any endpoint. Swagger injects `Authorization: Bearer <token>` automatically.

---

## Trying tenant isolation

The default `AUTH_TOKENS_JSON` (in `.env.example`) maps two tokens to two different orgs:

```
tok_alice → {user_id: alice, org_id: acme}
tok_bob   → {user_id: bob,   org_id: globex}
```

The agent's bearer token is controlled by `AGENT_AUTH_TOKEN` in `.env`.

**Demo:** ingest something as Alice, then flip to Bob and confirm the isolation:

```bash
# as Alice (default)
python -m agent.main "Ingest a doc titled 'Acme Internal Memo' with content: Board meeting postponed to next quarter."

# flip to Bob
AGENT_AUTH_TOKEN=tok_bob python -m agent.main "Search the corpus for board meeting."
# Bob's search returns zero or irrelevant results — Alice's doc is invisible to him.
```

---

## MCP tools exposed

### `rag-server` (5 tools, all prefixed `docs_`)

| Tool | Purpose |
|---|---|
| `docs_ingest(title, content)` | Chunk + embed + upsert into the caller's org corpus |
| `docs_search(query, top_k=5)` | Semantic search within the caller's org; returns top-k chunks (text truncated to 500 chars) |
| `docs_list(limit=20, cursor=None)` | Paginate documents (one entry per document, not per chunk) |
| `docs_get(document_id)` | Fetch full document; truncated if >8 KB with a hint to use `docs_search` |
| `docs_stats()` | Corpus metadata for the caller's org |

### `notes-server` (2 tools, all prefixed `notes_`)

| Tool | Purpose |
|---|---|
| `notes_create(text)` | Save a note in the caller's org workspace |
| `notes_list()` | List caller's notes, most recent first |

---

## Environment variables

Full reference in [`.env.example`](.env.example). Frequently-touched ones:

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `groq` | `groq` \| `anthropic` \| `ollama` |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Provider-specific model identifier |
| `GROQ_API_KEY` | _(unset)_ | Required if provider is `groq` |
| `ANTHROPIC_API_KEY` | _(unset)_ | Required if provider is `anthropic` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Used if provider is `ollama` |
| `RAG_MCP_URL` | `http://127.0.0.1:8000/mcp/sse` | Where the agent connects for RAG tools |
| `NOTES_MCP_URL` | `http://127.0.0.1:8001/mcp/sse` | Where the agent connects for notes tools |
| `AGENT_AUTH_TOKEN` | `tok_alice` | Bearer token the agent sends (must exist in `AUTH_TOKENS_JSON`) |
| `AUTH_TOKENS_JSON` | dev map | `{token: {user_id, org_id}}` resolved by both servers |
| `QDRANT_URL` | `http://localhost:6333` | |
| `QDRANT_COLLECTION` | `documents` | |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | 384-dim sentence-transformers model |
| `LANGSMITH_API_KEY` | _(unset)_ | Optional — enables LangSmith tracing |

---

## Project layout

```
.
├── CLAUDE.md                    Project goals + design calibration
├── NOTES.md                     Stage-by-stage learning log
├── README.md                    (this file)
├── pyproject.toml               PEP 621 metadata + deps
├── docker-compose.yml           Qdrant service
├── .env / .env.example
│
├── mcp_server/                  RAG MCP server (port 8000)
│   ├── server.py                FastAPI + FastMCP, lifespan, tool wrappers
│   ├── auth.py                  Bearer token -> identity via ContextVar
│   └── core/
│       ├── config.py            pydantic-settings
│       ├── embeddings.py        sentence-transformers singleton
│       ├── chunking.py          fixed-size chunker with overlap
│       └── state.py             Qdrant-backed RAG core (org-scoped)
│
├── notes_server/                Notes MCP server (port 8001)
│   └── server.py                self-contained; auth logic duplicated, not imported
│
└── agent/                       LangGraph ReAct agent
    ├── config.py                pydantic-settings (LLM, MCP URLs, observability)
    ├── llm.py                   get_llm() factory (groq | anthropic | ollama)
    ├── tools.py                 MultiServerMCPClient + session-lifecycle notes
    ├── observability.py         optional LangSmith
    ├── agent.py                 create_agent(...) -> CompiledStateGraph
    └── main.py                  CLI entrypoint, astream_events loop
```

---

## Common tasks

**Switch LLM provider.** Edit `.env`, change `LLM_PROVIDER` and `LLM_MODEL`, rerun the agent. No code changes.

**Reset the corpus.** `docker compose down -v` drops the Qdrant volume. Next start will recreate an empty collection.

**Inspect what the agent sees.** Keep both servers up and hit their Swagger UIs. The REST surface mirrors the MCP tools exactly — same state, same org filters.

**Add a new MCP tool to the RAG server.** Add a sync function in [`mcp_server/core/state.py`](mcp_server/core/state.py), then add an `@mcp.tool()`-decorated async wrapper in [`mcp_server/server.py`](mcp_server/server.py) that reads identity and calls it via `asyncio.to_thread`.

**Enable LangSmith tracing.** Add `LANGSMITH_API_KEY=...` to `.env`. Traces appear under the `mcp-agent-learning` project in LangSmith.

---

## Troubleshooting

**`401 Unauthorized` on Swagger "Try it out".** Click **Authorize** first and paste a bearer token (`tok_alice` or `tok_bob`). `/api/health` is the only unauthenticated endpoint.

**`Connection refused` to `localhost:6333`.** Qdrant isn't running — `docker compose up -d` and verify with `docker ps`.

**Embedding model download hangs on first request.** First `docs_ingest` or `docs_search` triggers a ~90 MB download from Hugging Face. Subsequent runs use the cache. Watch the server logs.

**Agent reports "unknown LLM_PROVIDER".** Check `.env`: value must be one of `groq`, `anthropic`, `ollama` (case-insensitive).

**Agent can't reach an MCP server.** `curl http://127.0.0.1:8000/api/health` and `curl http://127.0.0.1:8001/api/health` — both must return `{"status":"ok"}` before the agent will successfully open SSE sessions.

---

## Further reading

- [`CLAUDE.md`](CLAUDE.md) — project goals, design calibration (C1–C6), learning checkpoints.
- [`NOTES.md`](NOTES.md) — per-stage learning log: what landed, decisions worth remembering, smoke-test evidence.
- MCP spec: <https://modelcontextprotocol.io/>
- LangGraph docs: <https://langchain-ai.github.io/langgraph/>
- Qdrant payload-filtering docs: <https://qdrant.tech/documentation/concepts/filtering/>
