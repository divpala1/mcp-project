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

### Addendum — Swagger UI authorization

Both servers now expose a browser-testable Swagger UI at `/docs`.

**The mechanic.** Middleware does the real enforcement. FastAPI's
`HTTPBearer(auto_error=False)` attached as a route dependency does nothing
at runtime (the `auto_error=False` disables the dependency's own 401) —
its sole purpose is to make OpenAPI include a `components.securitySchemes`
entry so Swagger's "Authorize" button appears and the UI auto-injects the
`Authorization: Bearer …` header into "Try it out" requests.

**Why two layers instead of one.** The `/mcp/*` routes are a mounted Starlette
sub-app, not FastAPI routes, so FastAPI's dependency system can't reach
them. Middleware is the only layer that covers both /api/* and /mcp/*.
The Depends() on /api/* is purely a documentation hook on top of the
universal middleware enforcement.

**Exempt paths.** `/api/health`, `/docs`, `/redoc`, `/openapi.json`,
`/docs/oauth2-redirect` bypass the middleware — these are the static
pages needed to *load* Swagger in the first place. Auth happens *inside*
Swagger, per API call.

**How to use.** Open http://127.0.0.1:8000/docs (or :8001 for notes),
click Authorize, paste `tok_alice` or `tok_bob`, try any endpoint.

## Stage 4 — Agent (2026-04-23)

### What landed

- `agent/config.py` — pydantic-settings for LLM + MCP URLs + auth + observability.
- `agent/llm.py` — `get_llm()` factory. Lazy imports per provider branch;
  only the chosen provider's package is actually loaded.
- `agent/tools.py` — `MultiServerMCPClient` with bearer header on every
  SSE handshake. Big comment block on the 0.1.x → 0.2.x session-lifecycle
  shift (see below).
- `agent/observability.py` — optional LangSmith via env vars. No-op if
  `LANGSMITH_API_KEY` is unset. NOTE(observability) marker for where
  an eval harness would plug in later.
- `agent/agent.py` — `build_agent(llm, tools)` via `create_react_agent`.
  NOTE markers for planning, reflection, multi-agent, memory — one per
  extension point.
- `agent/main.py` — entrypoint. `astream_events(version="v2")` streams
  tokens + tool boundaries to stdout.

### Decisions worth remembering

**Session lifecycle: 0.1.x → 0.2.x inversion (checkpoint #1).**
CLAUDE.md describes the old pattern: `async with MultiServerMCPClient(...) as client:` block, agent runs inside. That was 0.1.x, when the client held one long-lived SSE session per server for the block's lifetime. `langchain-mcp-adapters` 0.2.x flipped the model: the client is stateless, each tool call opens a short-lived SSE session, does the JSON-RPC round-trip, and closes. The LangChain tools returned by `get_tools()` carry per-call session management internally, so they're safe to hold past any block. For a high-throughput agent you'd wrap the whole run in `async with` to skip per-call handshake cost; a learning project doesn't bother. The wire-level handshake steps (initialize → tools/call → close) are unchanged — we just do them per call now.

**Auth header goes on the connection config, not somewhere deeper.** `MultiServerMCPClient` accepts a `headers` dict per server. That header rides the SSE handshake on *every* tool call, which is exactly when our server-side auth middleware fires. One bearer token against both servers because AUTH_TOKENS_JSON is shared — the whole point of treating auth as transport-layer (C1).

**Tool schema conversion (checkpoint #3) happens for free.** `langchain-mcp-adapters` reads each MCP tool's JSON Schema, builds a pydantic args model, and wraps it in a `BaseTool`. No glue code on our side — `create_react_agent(llm, tools, ...)` accepts MCP-derived tools identically to any other LangChain tool.

**Why `create_react_agent` instead of a hand-built graph.** It gets us to a running agent in ~5 lines. The comments in `agent.py` mark exactly where the four common extensions slot in: `pre_model_hook` for planning, `post_model_hook` for reflection, `checkpointer` for message-history memory, and "compile as a sub-graph node" for multi-agent. When any one of those becomes necessary, we swap the prebuilt helper for a hand-built `StateGraph` with those nodes wired explicitly.

**Streaming via `astream_events(version="v2")` (checkpoint #6).** The event bus surfaces `on_chat_model_stream` (per-token), `on_tool_start`, `on_tool_end`. In a web UI these become websocket/SSE pushes; here we just print. Shows the correct *shape* of a production streaming agent without committing to a front-end.

### Learning checkpoints surfaced

- **#1 (MCP session lifecycle)** — full block in `agent/tools.py`.
- **#3 (tool schema conversion)** — in `agent/tools.py`.
- **#4 (llm.bind_tools)** — invoked implicitly by `create_react_agent`;
  noted in `agent/agent.py`.
- **#5 (ReAct in LangGraph)** — `agent/agent.py` docstring enumerates
  the 3 nodes and the conditional edge.
- **#6 (streaming)** — `agent/main.py` docstring + the event-handler loop.
- **#10 (LLM provider swap)** — `agent/llm.py` is the single chokepoint.
- **#11, #12 (memory + multi-agent extension points)** — NOTE markers in `agent.py`.

### Smoke test — Stage 5 merged (2026-04-23)

Prompt: *"Ingest a document titled 'AI Basics' with this content: … Then
search the corpus for neural networks. Finally, add a note saying I
completed a neural-networks search today."*

Observed:
1. `MultiServerMCPClient` loaded **7 tools** (`docs_ingest`, `docs_search`,
   `docs_list`, `docs_get`, `docs_stats`, `notes_create`, `notes_list`)
   from both servers in one call.
2. Agent called `docs_ingest` → RAG → new doc persisted to Qdrant.
3. Agent called `docs_search("neural networks", top_k=5)` → returned the
   just-ingested chunk at score 0.51; the older "Quantum Computing" doc
   came back at 0.11 and the LLM correctly flagged it as low relevance.
4. Agent called `notes_create` → note persisted to notes server's dict.
5. Agent streamed a final synthesis referencing all three tool results,
   token by token.

This one run exercises the full learning arc: provider-pluggable LLM →
multi-server MCP aggregation → org-scoped retrieval → structured tool
responses → streaming output. CLAUDE.md's Stage 5 target state is met.

### Addendum — migration to `langchain.agents.create_agent` (2026-04-23)

`langgraph.prebuilt.create_react_agent` is deprecated in 2026. Successor
is `langchain.agents.create_agent` from LangChain 1.x (added
`langchain>=1.2.0` to `pyproject.toml`).

**Why this is NOT a framework change.** `create_agent` still returns a
LangGraph `CompiledStateGraph`. It is LangGraph-backed internally. We
remain 100% on LangGraph primitives, which is the constraint for C3
(multi-agent readiness).

**API deltas:**
- `prompt=` → `system_prompt=`
- `pre_model_hook` / `post_model_hook` → `middleware=[…]`, a list of
  `AgentMiddleware` subclasses with `before_model` / `after_model` /
  `modify_model_request` hooks. Richer than a pair of scalar hooks.
- Added `name=` kwarg — pass it so the graph label propagates into
  LangSmith traces and supervisor graph nodes.
- `langchain.agents.middleware` ships ready-made middlewares:
  `HumanInTheLoopMiddleware`, `SummarizationMiddleware`,
  `LLMToolSelectorMiddleware` (tool retrieval — C2 future work),
  `ToolCallLimitMiddleware`, `ModelCallLimitMiddleware`, PII, etc.
  Useful as implementation references when we extend later.

**Behavioural note.** With the new API the agent dispatched three
independent tool calls (`docs_stats`, `docs_list`, `notes_create`) in
parallel. ToolNode has always supported that; the model's willingness
to emit multiple parallel tool_calls depends on the model + prompt.
Qwen3-32B on Groq did so cleanly here.

---

## Stage 5 — Third-Party / Hosted MCP Servers + Thinking Mode (2026-04-28)

### What landed

- **GitHub MCP** wired into `agent/config.py` as the `github` server entry. Uses
  `streamable_http` transport and a GitHub PAT carried as a `static_token` on the
  `McpServerSpec`. The server is omitted from the default set entirely when
  `GITHUB_PAT` is unset, so the agent runs clean without it.
- **LangChain Docs MCP** wired as `langchain_docs`. Public hosted server, no auth,
  `streamable_http`. Active whenever `LANGCHAIN_DOCS_MCP_URL` is non-empty.
- **`thinking_budget_tokens`** added to `AgentConfig`. Anthropic-only: when
  `enable_thinking=True` is passed per-request, `agent/llm.py` enforces
  `temperature=1` and `max_tokens >= budget` automatically (Anthropic requires both
  constraints when extended thinking is enabled). No-op for all other providers.
- `.env.example` updated with `GITHUB_MCP_URL`, `GITHUB_PAT`, and
  `LANGCHAIN_DOCS_MCP_URL` entries.

### Decisions worth remembering

**Two auth models in the same server dict (the split that matters).** The `rag` and
`notes` servers use the per-request user token: `build_mcp_client` injects the
caller's bearer straight from `run_agent(auth_token=...)`. The `github` server uses a
static PAT held in env — the same credential for every request. These two patterns
co-exist in `McpServerSpec` via the `static_token` field: when present,
`build_mcp_client` substitutes it for the per-request token for that server only.

The reason for the split: GitHub's MCP server has no concept of your app's users or
`org_id`. It authenticates the *agent* as a service account (the PAT owner), not the
human caller. Forwarding the user's opaque `tok_alice` bearer to GitHub would result
in a `401` on every call. `static_token` is the escape hatch for exactly this case.

**`streamable_http` vs `sse`.** Both GitHub MCP and LangChain Docs MCP use
`streamable_http` — the MCP spec's newer transport. The wire shape is similar to SSE
(NDJSON over HTTP), but the framing and session model differ. `langchain-mcp-adapters`
handles the difference transparently; the only configuration change is
`"transport": "streamable_http"`. Local servers built with FastMCP still use `"sse"`.

**LangChain Docs server silently ignores the user bearer.** `build_mcp_client`
injects the per-request bearer for `langchain_docs` (no `static_token`, so default
behaviour applies). The public server simply ignores any `Authorization` header it
receives. This is harmless — the header goes out, gets discarded, no error. We noted
it in comments rather than adding special-casing: a `no_auth=True` flag on the spec
would be marginally cleaner but adds complexity for one server.

**Thinking budget as a deployment constant.** `thinking_budget_tokens` lives in
`AgentConfig` (env-backed) rather than being a per-request argument. The reasoning:
the budget is a cost/latency knob that the operator controls at deployment time — not
something callers should be able to set arbitrarily (it directly affects token billing
and response latency). If a per-request override is ever needed, pass it through a
custom endpoint.

### Learning checkpoints surfaced

- **C2b (multi-server)** — extended to three server types: local SSE, hosted
  Streamable HTTP with per-request user token (LangChain Docs), and hosted Streamable
  HTTP with static service credential (GitHub). All three co-exist in the same
  `McpServerSpec` dict without any shared code changes.
- **C4 (provider swap)** — `thinking_budget_tokens` is Anthropic-specific; `llm.py`
  guards it behind `if provider == "anthropic":`, keeping the other provider branches
  clean.

---

## Stage 6 — Local Tool Registry + Tool Composition Seam (2026-04-28)

### What landed

- **`agent/registry.py`** — a tiny module-level dict of `name → BaseTool`. Public
  API is three functions: `register(tool)` (works as a decorator on top of
  `@tool`), `registered_tools()` (flat list), `unregister(name)` / `clear()`.
  Re-registering an existing name logs a warning and replaces — chosen over a
  hard error so dev hot-reload doesn't crash the process.
- **`agent/toolset.py`** — `compile_tools(mcp_servers=..., auth_token=...)` is
  the new single seam responsible for producing the final tool list. Pulls from
  two sources: MCP servers (via `agent/tools.py`) and the local registry. Returns
  `(tools, reason)` — `reason` is a human-readable string the no-tool prompt uses
  to explain failure modes to the LLM. The function never re-raises, so a
  flaky MCP server can't crash the streaming loop.
- **`agent/core.py`** simplified: the inline 25-line MCP-loading block is now a
  single `await compile_tools(...)` call. Behaviour is unchanged — same two
  failure modes (no servers configured / load failed), same model-facing reasons.
- All affected guide markdowns updated: `CLAUDE.md` (project layout), `README.md`
  (project layout + feature list + how-to), `DRYRUN.md` (request trace),
  `agent/WALKTHROUGH.md` (file map, step list, dependency diagram, Q&A),
  `agent/prompts/WALKTHROUGH.md` (the `core.py` snippet at "How it hooks in").

### Decisions worth remembering

**Why two new files, not one.** `registry.py` and `toolset.py` have distinct
responsibilities. The registry is a passive collection — modules anywhere in
the codebase add to it at import time. `compile_tools` is an active orchestrator
that mixes the registry with a network-bound MCP loader and (in future) a
tool-finder. Keeping them separate means the registry has zero MCP/network
imports and is safe to import from anywhere; `toolset.py` is the only thing
that pulls in `langchain-mcp-adapters`.

**Why `compile_tools` returns a reason instead of raising.** The previous
inline implementation already swallowed MCP errors and turned them into
`notools_reason`. Lifting that contract into the function signature
(`tuple[list[BaseTool], str | None]`) makes the no-throw guarantee explicit.
Callers don't need a `try` block; the streaming loop in `core.py` is simpler
as a result.

**Why the tool-finder seam lives in `compile_tools`, not as a wrapper around
`run_agent`.** The finder needs the merged tool list (MCP + registry) to rank
against the user's query. Putting it inside `compile_tools` means the rest of
the codebase sees one filtered list and never has to know whether filtering
happened. When the finder lands, the change is `tools = await
finder.rank(tools, query, top_k=K)` — one line, in the marked spot.

**Decorator API.** `register` returns the tool unchanged so it can stack on top
of `@tool`. We validate that the input is a `BaseTool` (TypeError otherwise) so
that `register(my_func)` (forgot the `@tool`) fails immediately instead of
later when the LLM tries to bind a non-tool object.

### Learning checkpoints surfaced

- **C2a (tool explosion / future retrieval)** — `compile_tools` is now the
  single, marked place where a tool-finder layer slots in. The shape stays
  `list[BaseTool] -> list[BaseTool]`, so adding it doesn't ripple.
- **Composition over coupling** — the previous code had `core.py` directly
  calling `build_mcp_client` and `load_tools`. Now `core.py` knows nothing
  about MCP; it asks `toolset` for tools. That's the same shape we'll want
  when the agent grows new tool sources (e.g. plugin loaders, dynamically
  fetched MCP catalogs).
