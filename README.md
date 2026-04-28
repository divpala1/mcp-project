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
| **`agent`** ([`agent/`](agent/)) | LangGraph ReAct agent. Connects to both MCP servers via SSE, aggregates tools, streams events. Provider-pluggable (Groq / Anthropic / Ollama) via one env var. Runs as **CLI** (`python -m agent.main`) or **FastAPI service** (mount `agent.api.router` in any host). | CLI / `8002` |

Two additional servers are pre-wired as **optional external integrations** (no local process required — they are hosted third-party endpoints):

| External server | Role | Endpoint |
|---|---|---|
| **`github-mcp`** | GitHub's official hosted MCP server — repos, issues, PRs, code search, file browsing. Requires a GitHub PAT. | `api.githubcopilot.com/mcp/` |
| **`langchain-docs-mcp`** | LangChain's public docs MCP server — real-time search over LangChain, LangGraph, and LangSmith docs. No auth required. | `docs.langchain.com/mcp` |

Supporting infrastructure:

- **Qdrant** — vector DB, runs in Docker via [`docker-compose.yml`](docker-compose.yml).

---

## Features

- **Tenant isolation** — every Qdrant query filters by `org_id`; guessing another org's `document_id` returns "not found". Enforced at a single chokepoint in [`mcp_server/core/state.py`](mcp_server/core/state.py).
- **Bearer-token auth, end-to-end** — the FastAPI surface forwards the caller's `Authorization` header straight through to MCP, so org-scoping holds across multiple users on a shared deployment. CLI uses `AGENT_AUTH_TOKEN` for the same plumbing in single-user mode.
- **Embeddable agent** — `agent/` is a self-contained module. The framework-free `run_agent(...)` callable (in [`agent/core.py`](agent/core.py)) yields a structured event stream any host can consume; the optional `APIRouter` (in [`agent/api.py`](agent/api.py)) drops into any FastAPI app with one `include_router` call.
- **External/hosted MCP servers** — GitHub's MCP and LangChain's docs MCP are pre-wired alongside the local servers. Demonstrates the `static_token` pattern (service credential held in env, same for every user) sitting next to the per-request user-token pattern (`rag`/`notes`). See [`agent/config.py`](agent/config.py) for the `McpServerSpec` auth-model docstring.
- **Tool namespacing** — `docs_*` on the RAG server, `notes_*` on the notes server. No collisions when `MultiServerMCPClient` merges tool lists.
- **Huge-data patterns** — pagination cursors, per-tool response-size caps, structured truncation with hints.
- **Streaming** — token-by-token output via LangGraph's `astream_events`, surfaced as SSE for the FastAPI path and emoji-decorated stdout for the CLI.
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

### Terminal 3b — the agent (CLI)

```bash
source venv/bin/activate
python -m agent.main "Ingest a document titled 'Quantum Computing' with content: Qubit entanglement is foundational to quantum computing. Then search for qubit entanglement. Finally, add a note saying I did this search today."
```

The agent will:
1. Load tools across all configured MCP servers — 7 base tools from `rag` + `notes`, plus GitHub tools if `GITHUB_PAT` is set, plus LangChain Docs tools if `LANGCHAIN_DOCS_MCP_URL` is set.
2. Call `docs_ingest` (RAG).
3. Call `docs_search` (RAG).
4. Call `notes_create` (notes).
5. Stream a synthesised final answer token-by-token.

The CLI reads its bearer token from `AGENT_AUTH_TOKEN` in `.env` — that's the dev-mode shortcut, not how production callers authenticate (see below).

---

## Running the agent as a FastAPI service

The agent ships a ready-to-mount FastAPI router so it can be embedded in any host app — including, eventually, a separate production codebase. There's also a tiny standalone host ([`agent/app.py`](agent/app.py)) for end-to-end testing in this repo.

### Standalone (3-line host, for testing)

```bash
source venv/bin/activate
uvicorn agent.app:app --host 127.0.0.1 --port 8002
```

That boots a FastAPI app whose only route is `POST /agent/chat`, an SSE-streaming endpoint. Send a prompt with the caller's bearer token in the `Authorization` header:

```bash
curl -N -X POST http://127.0.0.1:8002/agent/chat \
  -H "Authorization: Bearer tok_alice" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Search for qubit entanglement and add a note about it."}'
```

The response is a stream of `data: {...}\n\n` SSE frames, one per `AgentEvent`:

| Event `type` | Other fields | When it fires |
|---|---|---|
| `token` | `text` | One per LLM token as it streams |
| `tool_start` | `name`, `args` | Right before a tool is invoked |
| `tool_end` | `name`, `output` | After the tool returns |
| `error` | `message` | Anything raised during the run (auth rejection, LLM/network failure). The stream still terminates cleanly. |
| `end` | — | Always last frame |

OpenAPI docs at <http://127.0.0.1:8002/docs>.

### Embedding in another FastAPI app

The same router is what production hosts mount. Two patterns, depending on how much control the host needs:

```python
# 1. Drop-in mount — gets POST /agent/chat with the default contract.
from fastapi import FastAPI
from agent.api import router

app = FastAPI()
app.include_router(router)

# 2. Custom endpoint — when you need different middleware, your own auth
#    layer, custom request shape, or per-user MCP-server resolution.
from agent import run_agent

@app.post("/my-chat")
async def chat(req: MyRequest, user: AuthenticatedUser = Depends(...)):
    servers = await resolve_mcp_servers_for_user(user)  # production-side logic
    async def stream():
        async for ev in run_agent(req.prompt, auth_token=user.token, mcp_servers=servers):
            yield format_however_you_want(ev)
    return StreamingResponse(stream(), media_type="text/event-stream")
```

### Auth model

| Caller | How the bearer token reaches MCP |
|---|---|
| **CLI** (`python -m agent.main`) | Reads `AGENT_AUTH_TOKEN` from env, passes to `run_agent(..., auth_token=...)`. |
| **FastAPI (drop-in router)** | Reads `Authorization: Bearer <token>` header and forwards verbatim. |
| **FastAPI (custom endpoint)** | Host extracts identity however it likes (header, JWT, session) and passes a token string to `run_agent(...)`. |

The agent never validates the token itself — the MCP server (`mcp_server/auth.py`) is the single source of truth on identity. The agent only needs to forward whatever opaque string it's given.

### Config: deployment-level vs. per-request

The split is the same one production services tend to land on:

| Layer | Where it lives | Examples |
|---|---|---|
| **Deployment-level** (env, set at startup) | [`agent/config.py`](agent/config.py) | `LLM_PROVIDER`, `LLM_MODEL`, API keys, LangSmith |
| **Per-request** (function/endpoint inputs) | `run_agent(...)` args | `prompt`, `auth_token` |
| **Hybrid** (env default + per-request override) | `run_agent(mcp_servers=...)` | The MCP server set. The drop-in router doesn't expose this — production hosts that need per-user resolution write a custom endpoint and pass the dict directly. |

The endpoint deliberately does **not** accept `llm_provider`, `llm_model`, or arbitrary MCP URLs as request body fields — those would either leak deployment internals or invite SSRF. They stay on the server side.

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

### `github-mcp` (GitHub's official hosted server — optional)

Active when `GITHUB_PAT` is set in `.env`. Uses `streamable_http` transport with a **static service credential** (the PAT) rather than the per-request user token. The tool set depends on the PAT's scopes; typical read-only tools include `get_file_contents`, `search_code`, `list_issues`, `get_pull_request`, `create_issue`, and `search_repositories`, among others.

This server illustrates the second auth model in `McpServerSpec`: the agent holds one fixed service credential and acts as a service account, rather than forwarding each caller's own identity. The GitHub server has no concept of your app's `org_id` — every request authenticates as whoever owns the PAT.

See the [GitHub MCP server repo](https://github.com/github/github-mcp-server) for the full tool reference and required scopes.

### `langchain-docs-mcp` (LangChain's public docs server — always active)

Active whenever `LANGCHAIN_DOCS_MCP_URL` is non-empty (default: `https://docs.langchain.com/mcp`). Uses `streamable_http` transport, **no auth**. Provides real-time semantic search over LangChain, LangGraph, and LangSmith documentation — particularly useful when the agent is answering questions about the frameworks this project is built on.

Because the server ignores any `Authorization` header it receives, no `static_token` is needed — `build_mcp_client` still injects the user bearer by default, but the server simply discards it. Blank the env var to exclude this server from the default tool catalog.

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
| `RAG_MCP_URL` | `http://127.0.0.1:8000/mcp/sse` | Default RAG MCP endpoint (overridable per-call via `run_agent(mcp_servers=...)`) |
| `NOTES_MCP_URL` | `http://127.0.0.1:8001/mcp/sse` | Default notes MCP endpoint (same override path) |
| `GITHUB_MCP_URL` | `https://api.githubcopilot.com/mcp/` | GitHub hosted MCP endpoint. Override only if GitHub moves it. |
| `GITHUB_PAT` | _(unset)_ | GitHub Personal Access Token. When set, adds the `github` MCP server to the default set using a **static service credential** (not the per-request user token). Create a fine-grained PAT at github.com/settings/tokens. Leave blank to exclude GitHub tools entirely. |
| `LANGCHAIN_DOCS_MCP_URL` | `https://docs.langchain.com/mcp` | LangChain Docs MCP endpoint. Blank to exclude from tool catalog. No auth required. |
| `AGENT_AUTH_TOKEN` | `tok_alice` | **CLI-only.** Bearer token used by `python -m agent.main`. Production callers forward `Authorization` headers and don't set this. |
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
└── agent/                       LangGraph ReAct agent (CLI + embeddable FastAPI)
    ├── __init__.py              public API: run_agent, AgentEvent, McpServerSpec
    ├── config.py                pydantic-settings + default_mcp_servers() helper
    ├── llm.py                   get_llm() factory (groq | anthropic | ollama), memoized
    ├── tools.py                 build_mcp_client(servers, *, auth_token), per-request
    ├── observability.py         optional LangSmith
    ├── agent.py                 create_agent(...) -> CompiledStateGraph
    ├── core.py                  framework-free run_agent() async generator
    ├── api.py                   optional FastAPI APIRouter (POST /agent/chat, SSE)
    ├── app.py                   3-line standalone host for local testing
    ├── main.py                  CLI entrypoint — renders run_agent events to stdout
    └── prompts/
        ├── __init__.py          registry: get_prompt(), get_prompt_version(), render_tool_catalog()
        └── system.md            system prompt template (v2); {tool_catalog} filled at runtime
```

---

## Common tasks

**Switch LLM provider.** Edit `.env`, change `LLM_PROVIDER` and `LLM_MODEL`, rerun the agent. No code changes.

**Reset the corpus.** `docker compose down -v` drops the Qdrant volume. Next start will recreate an empty collection.

**Inspect what the agent sees.** Keep both servers up and hit their Swagger UIs. The REST surface mirrors the MCP tools exactly — same state, same org filters.

**Add a new MCP tool to the RAG server.** Add a sync function in [`mcp_server/core/state.py`](mcp_server/core/state.py), then add an `@mcp.tool()`-decorated async wrapper in [`mcp_server/server.py`](mcp_server/server.py) that reads identity and calls it via `asyncio.to_thread`.

---

## Adding a new MCP server to the agent

This is the full checklist for wiring an additional MCP server into the agent. The steps are the same whether you are running a local server you built yourself or connecting to a third-party hosted one.

### 1. Choose a transport

The agent supports two transports:

| Transport | `"transport"` value | When to use |
|---|---|---|
| Server-Sent Events | `"sse"` | Local servers built with FastMCP / this project's pattern |
| Streamable HTTP | `"streamable_http"` | Modern hosted servers (e.g. GitHub MCP, LangChain Docs MCP, Anthropic remote MCP) |

Check your server's docs. If it exposes a `/sse` endpoint, use `"sse"`. If it exposes a plain HTTP endpoint that streams JSON, use `"streamable_http"`.

**Note:** GitHub MCP and LangChain Docs MCP are already pre-wired in `agent/config.py` — if you want to connect to one of those two specifically, just set the relevant env vars (`GITHUB_PAT` for GitHub, or ensure `LANGCHAIN_DOCS_MCP_URL` is set). The steps below are for adding a *new* server that isn't already registered.

### 2. Decide on the auth model

There are two patterns (documented in [`agent/config.py`](agent/config.py)):

- **Per-request user token (default).** The token the caller passes to `run_agent()` is forwarded to this server. Use this when the server uses the bearer to identify *who the user is* — e.g. your own RAG/notes servers that scope results by `org_id`.
- **Static service credential.** A fixed credential held in env, independent of the caller. Use this when the server expects a service account — e.g. a GitHub PAT. Set `static_token` on the spec. GitHub MCP uses this pattern.

### 3. Add the env vars

Open `.env` (or `.env.example` for documentation purposes) and add the new URL and, if applicable, the static token:

```bash
# .env
MY_SERVER_MCP_URL=http://127.0.0.1:8002/mcp/sse  # or https://... for hosted
MY_SERVER_TOKEN=sk-...                             # only if using a static token
```

### 4. Register the server in `agent/config.py`

Add a field for the URL (and optionally the token) to `AgentConfig`, then wire it into `default_mcp_servers()`:

```python
# In AgentConfig:
my_server_mcp_url: str = ""
my_server_token: str | None = None   # omit if using per-request user token

# In default_mcp_servers():
if settings.my_server_mcp_url:
    spec: McpServerSpec = {
        "url": settings.my_server_mcp_url,
        "transport": "sse",            # or "streamable_http"
    }
    if settings.my_server_token:
        spec["static_token"] = settings.my_server_token
    mcp_servers["my_server"] = spec
```

The dict key (`"my_server"`) becomes the **namespace prefix** the agent sees. See step 5.

### 5. Namespace the tools on the server side

Tool names from all servers are merged into a single flat list by `MultiServerMCPClient`. Collisions cause the LLM to pick the wrong tool. Prefix every tool name with the namespace you chose in step 4:

```python
# On your server (FastMCP example):
@mcp.tool()
async def my_server_do_something(...):
    ...
```

Existing conventions: `docs_*` for the RAG server, `notes_*` for the notes server. Keep the same `<namespace>_<verb>` pattern.

### 6. Start the new server and verify

```bash
# Start your server
uvicorn my_package.server:app --host 127.0.0.1 --port 8002

# Confirm it's up — MCP servers in this project expose a health endpoint
curl http://127.0.0.1:8002/api/health   # → {"status":"ok"}
```

### 7. Run the agent and confirm tool discovery

```bash
python -m agent.main "List all tools you have available."
```

The agent's system prompt includes a live tool catalog rendered at startup. You should see your new tools listed under their namespace. If they are missing, check:

1. The server is reachable from the agent (`curl` the health endpoint).
2. `MY_SERVER_MCP_URL` is set in `.env` and the URL ends in the correct path (e.g. `/mcp/sse`).
3. `default_mcp_servers()` includes the new entry (add a `print` or check logs if unsure).
4. There are no SSE/HTTP errors in the server's terminal — the MCP handshake (`initialize` → `tools/list`) happens at session open, not at tool call time.

### Passing a custom server set per-call (no env vars)

If you want to add a server only for a specific invocation — without touching config — pass `mcp_servers` directly to `run_agent`:

```python
from agent import run_agent
from agent.config import McpServerSpec

extra: dict[str, McpServerSpec] = {
    "my_server": {
        "url": "http://127.0.0.1:8002/mcp/sse",
        "transport": "sse",
        # "static_token": "sk-..." if needed
    }
}

async for event in run_agent("Do something.", auth_token="tok_alice", mcp_servers=extra):
    print(event)
```

This is the recommended pattern for production endpoints that resolve the MCP server set dynamically per user.

**Edit the system prompt.** Open [`agent/prompts/system.md`](agent/prompts/system.md), change the text, and bump the `version:` integer in the frontmatter. The next process start picks it up (prompts are cached per-process, not per-request — restart uvicorn to reload when running as a service). The version number is recorded as `system@vN` in every LangSmith trace so you can compare prompt iterations across runs.

**Enable LangSmith tracing.** Add `LANGSMITH_API_KEY=...` to `.env`. Traces appear under the `mcp-agent-learning` project in LangSmith.

**Embed the agent in another FastAPI app.** `from agent.api import router` then `app.include_router(router)` — that adds `POST /agent/chat`. Or `from agent import run_agent` and write your own endpoint when you need custom auth, request shape, or per-user MCP-server resolution. See the [Running the agent as a FastAPI service](#running-the-agent-as-a-fastapi-service) section.

---

## Troubleshooting

**`401 Unauthorized` on Swagger "Try it out".** Click **Authorize** first and paste a bearer token (`tok_alice` or `tok_bob`). `/api/health` is the only unauthenticated endpoint.

**`Connection refused` to `localhost:6333`.** Qdrant isn't running — `docker compose up -d` and verify with `docker ps`.

**Embedding model download hangs on first request.** First `docs_ingest` or `docs_search` triggers a ~90 MB download from Hugging Face. Subsequent runs use the cache. Watch the server logs.

**Agent reports "unknown LLM_PROVIDER".** Check `.env`: value must be one of `groq`, `anthropic`, `ollama` (case-insensitive).

**Agent can't reach an MCP server.** `curl http://127.0.0.1:8000/api/health` and `curl http://127.0.0.1:8001/api/health` — both must return `{"status":"ok"}` before the agent will successfully open SSE sessions.

**`POST /agent/chat` returns 401 with no auth header.** Expected — the FastAPI surface requires `Authorization: Bearer <token>`. The agent only checks the header is present and well-formed; the MCP server is what actually validates the token, so an unknown token surfaces as an `error` event mid-stream rather than a 401.

**GitHub tools missing from the agent's tool catalog.** `GITHUB_PAT` must be non-empty in `.env` for the `github` server to join the default set. Verify with `python -c "from agent.config import default_mcp_servers; print(list(default_mcp_servers()))"` — you should see `"github"` in the list. Also confirm the PAT hasn't expired and has the necessary scopes for the tools you want to call.

**Agent fails with a `403` or `401` on GitHub tool calls.** The PAT is valid but lacks required scopes. GitHub's MCP server maps tool permissions to PAT scopes — e.g. `list_issues` needs `repo` (or `issues: read` on a fine-grained PAT). Check the [GitHub MCP server docs](https://github.com/github/github-mcp-server) for the scope map.

---

## Further reading

- [`CLAUDE.md`](CLAUDE.md) — project goals, design calibration (C1–C6), learning checkpoints.
- [`NOTES.md`](NOTES.md) — per-stage learning log: what landed, decisions worth remembering, smoke-test evidence.
- MCP spec: <https://modelcontextprotocol.io/>
- LangGraph docs: <https://langchain-ai.github.io/langgraph/>
- Qdrant payload-filtering docs: <https://qdrant.tech/documentation/concepts/filtering/>
