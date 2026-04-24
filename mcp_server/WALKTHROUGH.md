# RAG MCP Server Walkthrough

This document explains the `mcp_server/` package file by file, and traces a
single request from the moment the agent sends a bearer token to the moment
a Qdrant result flows back over SSE.

---

## The big picture

The RAG MCP server is a single FastAPI process that exposes two surfaces:

```
http://127.0.0.1:8000
├── /api/*        REST endpoints (curl-able, for debugging)
└── /mcp/*        MCP SSE transport (what the agent actually uses)
      ├── GET  /mcp/sse          open the SSE stream (auth fires here)
      └── POST /mcp/messages/    JSON-RPC calls (tools/list, tools/call)
```

Both surfaces share the same auth layer, the same Qdrant client, and the same
embedding model. Running them in one process means one startup cost and no
network hop between the MCP handler and the Qdrant query.

### File map

```
mcp_server/
├── server.py          FastAPI app + FastMCP tools — the front door
├── auth.py            Bearer token → identity via ContextVar
└── core/
    ├── config.py      pydantic-settings, validated at import
    ├── state.py       Qdrant reads/writes, chunking, embedding (the engine)
    ├── embeddings.py  sentence-transformers wrapper (singleton model)
    └── chunking.py    fixed-size word chunker
```

---

## How a single tool call flows through the server

Here is the full path for a `docs_search` call:

```
Agent (HTTP client)
  │
  │  GET /mcp/sse  Authorization: Bearer tok_alice
  ▼
Starlette middleware (auth.auth_middleware)
  │  resolve token → {user_id: "alice", org_id: "acme"}
  │  stash identity in ContextVar (current_identity)
  ▼
FastMCP SSE handler
  │  MCP handshake: initialize → tools/list
  │  (later) tools/call  docs_search  {query: "qubit", top_k: 3}
  ▼
docs_search tool (server.py)
  │  auth.require_identity() reads ContextVar → org_id = "acme"
  │  asyncio.to_thread(state.search_documents, "qubit", "acme", 3)
  ▼
state.search_documents (core/state.py)
  │  embeddings.embed_one("qubit") → 384-dim vector
  │  Qdrant query_points(filter={org_id: "acme"}, limit=3)
  │  truncate text to 500 chars, flag text_truncated
  ▼
JSON result → FastMCP JSON-RPC response → SSE event → agent
```

---

## Step 1 — Config (`core/config.py`)

`ServerConfig` is a pydantic-settings class that reads `.env` at import time.
If `AUTH_TOKENS_JSON` is missing or malformed JSON, the process crashes before
serving a single request — the `@field_validator` catches this.

Key fields:

| Field              | What it holds                                      |
|--------------------|----------------------------------------------------|
| `auth_tokens_json` | Raw JSON string; parsed into `auth_tokens` property |
| `qdrant_url`       | Where Qdrant is running                            |
| `qdrant_collection`| Collection name (all orgs share one collection)    |
| `embedding_model`  | sentence-transformers model name                   |

**Why one collection for all orgs?**  
Per-org collections would be cleaner isolation but require DDL (collection
creation) every time a new org onboards. One shared collection with a payload
filter is operationally simpler and scales fine unless you need strict
noisy-neighbour or compliance isolation — at which point you'd switch to
collection-per-tenant. There's a `# NOTE` about this in `state.py`.

---

## Step 2 — Auth (`auth.py`)

This is **learning checkpoint #2: auth is a transport-layer concern.**

### Why MCP has no native auth

The MCP spec defines a protocol for capability negotiation and tool invocation.
It says nothing about which user is calling. Identity is entirely up to the
transport (HTTP in our case). This is intentional — MCP stays protocol-neutral.

### How we implement it

```
.env: AUTH_TOKENS_JSON = {"tok_alice": {"user_id": "alice", "org_id": "acme"}}

Agent → Authorization: Bearer tok_alice
           │
           ▼
    auth_middleware
       strip "Bearer "
       look up token in auth_tokens dict
       set current_identity ContextVar to {"user_id": "alice", "org_id": "acme"}
       forward request
           │
           ▼
    tool handler
       auth.require_identity() → reads ContextVar
       passes org_id to state.* functions
```

### Why `ContextVar`?

The alternative is threading `Request` through every function signature — which
would make `state.py` depend on FastAPI, making it untestable without an HTTP
server. `ContextVar` is:

- Per-asyncio-task, so two concurrent requests don't see each other's identity.
- Thread-safe, so `asyncio.to_thread` calls preserve the value (Python copies
  the context into the new thread automatically).
- Zero-pollution: `state.py` never imports FastAPI or knows HTTP exists.

### The `finally` block matters

```python
ctx_tok = current_identity.set(identity)
try:
    return await call_next(request)
finally:
    current_identity.reset(ctx_tok)
```

`reset(ctx_tok)` restores the ContextVar to whatever it was before `set()` —
in production, that's `None`. Without this, a task that gets reused (asyncio
task pooling) could carry a stale identity into the next request. The
`try/finally` guarantees cleanup even if the request handler raises.

### What `UNAUTHED_PATHS` is for

`/api/health` is a liveness probe — monitoring systems call it without tokens.
`/docs` and `/openapi.json` are Swagger's static HTML and schema pages.
Authentication inside Swagger works through its "Authorize" button, which
injects a bearer token into individual API calls — not into the page load itself.
So the pages must be reachable unauthenticated; the *protected routes* enforce
the token.

---

## Step 3 — The FastAPI app and lifespan (`server.py`)

### Lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(state.ensure_collection)
    yield
```

FastAPI's lifespan event is the right place for startup work:

- Runs once, before the first request is served.
- If Qdrant is down or the embedding model can't load, the process fails here
  with a clear error — not halfway through the first ingest call.
- The `asyncio.to_thread` bridges the sync `QdrantClient` call into the async
  startup context without blocking the event loop.

### Why `asyncio.to_thread` everywhere

`QdrantClient` and `SentenceTransformer` are synchronous libraries. FastAPI
handlers are async. Calling a sync library directly from an async function
blocks the event loop — no other request can be served until the call returns.
`asyncio.to_thread` runs the sync function in a thread-pool worker, letting
the event loop stay free. For a learning project with a handful of concurrent
requests this is "good enough and simple"; a high-throughput service would use
an async Qdrant client instead.

### Middleware registration

```python
app.middleware("http")(auth.auth_middleware)
```

Starlette (FastAPI's underlying framework) runs middleware before routing. This
means `auth_middleware` fires on every request — both the `/api/*` REST routes
and the `/mcp/*` SSE endpoints — without needing to add a `Depends()` to each
individually. The middleware approach is what makes the MCP SSE transport
protected without FastMCP needing to know about auth.

### `HTTPBearer(auto_error=False)` in `Depends`

The `Depends(bearer_scheme)` on REST routes is **documentation only**. It tells
OpenAPI that the route requires a bearer token, which makes Swagger show a padlock
icon and lets the "Authorize" button pre-fill the header. `auto_error=False` means
it won't reject requests on its own — the actual enforcement is in `auth_middleware`.
Without this Depends, Swagger has no way to know the route is protected.

### MCP mount

```python
mcp = FastMCP("rag-server")
# ... tool definitions ...
app.mount("/mcp", mcp.sse_app())
```

`FastMCP` is a thin wrapper from the `mcp` package. Decorating a function with
`@mcp.tool()` registers it: FastMCP reads the function's type hints and docstring
to generate a JSON Schema automatically. `mcp.sse_app()` returns a Starlette
sub-app that speaks the MCP SSE transport — GET `/sse` opens the stream, POST
`/messages/` receives JSON-RPC. Mounting it at `/mcp` makes the full path
`/mcp/sse` and `/mcp/messages/`, which is what the agent's config points to.

---

## Step 4 — Tools (`server.py` continued)

All five MCP tools follow the same three-line shape:

```python
@mcp.tool()
async def docs_search(query: str, top_k: int = 5) -> list[dict]:
    """...docstring becomes the MCP tool description..."""
    org_id = auth.require_identity()["org_id"]
    return await asyncio.to_thread(state.search_documents, query, org_id, top_k)
```

1. **Read identity** — never trust caller-supplied `org_id`; always pull from
   the authenticated ContextVar. This is the enforcement point for C1.
2. **Delegate to `state.*`** — the tool wrapper does no business logic.
3. **`asyncio.to_thread`** — bridges sync state functions into the async handler.

### Tool namespacing (`docs_*`)

Every tool is prefixed `docs_`. When `MultiServerMCPClient` aggregates tools
from the RAG server and the notes server, the agent's tool list looks like:

```
docs_ingest   docs_search   docs_list   docs_get   docs_stats
notes_create  notes_list
```

No collisions, no disambiguation glue, and the LLM can infer from the name
alone which server a tool belongs to.

---

## Step 5 — The engine (`core/state.py`)

### Data model in Qdrant

One **Qdrant point** per chunk. Each point has:

| Field         | Type    | Purpose                                          |
|---------------|---------|--------------------------------------------------|
| `id`          | UUID    | Unique point ID (Qdrant requires it)             |
| `vector`      | float[] | 384-dim sentence-transformers embedding          |
| `org_id`      | string  | Tenant isolation — every query filters on this   |
| `document_id` | UUID    | Groups all chunks of one document                |
| `title`       | string  | Human-readable document label                    |
| `chunk_index` | int     | Position in document (0 = first chunk)           |
| `total_chunks`| int     | How many chunks this document was split into     |
| `text`        | string  | The chunk's raw text                             |

`chunk_index == 0` is the "header" chunk. `list_documents` and `describe_corpus`
filter to only `chunk_index == 0` so they touch one point per document instead
of scanning all chunks.

### Tenant isolation — the single chokepoint (C1)

```python
def _org_filter(org_id: str) -> Filter:
    return Filter(must=[
        FieldCondition(key="org_id", match=MatchValue(value=org_id)),
    ])
```

`_org_filter` is called in **every** read operation. There is no code path that
returns data without scoping to an `org_id`. A user guessing another org's
`document_id` will hit a `not found` error — the wrong-org documents simply
don't appear in their filtered results.

Payload indexes (`create_payload_index` in `ensure_collection`) make these
filtered queries O(log n) instead of O(n) — Qdrant maintains a B-tree per
indexed field. For a dev corpus with a few hundred points the difference is
invisible; for millions of points it's significant.

### Ingest (`ingest_document`)

```
content
  │
  ▼  chunk_text()      → ["chunk 0 words...", "chunk 1 words...", ...]
  │
  ▼  embeddings.embed()→ [[0.12, -0.04, ...], ...]   (one vector per chunk)
  │
  ▼  QdrantClient.upsert(points=[...], wait=True)
```

`wait=True` means the method blocks until the write is durable. For a learning
project this gives a simple mental model: once `ingest_document` returns, the
chunks are searchable. A high-throughput ingestion pipeline would use `wait=False`
and batch writes.

### Search (`search_documents`)

```python
qv = embeddings.embed_one(query)           # embed the query the same way as docs
results = _qc().query_points(
    query=qv,
    query_filter=_org_filter(org_id),      # C1: only this org's chunks
    limit=top_k,
)
```

Similarity search works by comparing the query vector to every stored chunk vector
using cosine similarity. Qdrant returns the top-k closest chunks with a score in
[0, 1] (higher = more similar). The query and the document chunks were embedded
with the same model, so the vector space is compatible.

**C5 pattern:** each chunk's text is capped at 500 characters. If truncated,
`text_truncated: true` is set. The agent sees this flag and can call `docs_get`
for the full document if it needs more than the snippet.

### List + paginate (`list_documents`)

```python
points, next_offset = _qc().scroll(
    scroll_filter=_org_headers_filter(org_id),   # chunk_index == 0 only
    limit=limit,
    offset=cursor,                               # opaque Qdrant offset
)
```

Qdrant's `scroll` is the equivalent of SQL `LIMIT/OFFSET` but cursor-based
(stable across inserts/deletes). `next_offset` is an opaque point ID the caller
passes back as `cursor` to get the next page. The agent decides whether to keep
paging based on `total` and whether it has seen enough results.

### Get full document (`get_document`)

Fetches all chunks for a `document_id` in one `scroll`, sorts by `chunk_index`,
and joins the text. The 8 KB response cap prevents a large document from filling
the agent's context. When truncated, the response includes:

```json
{
  "truncated": true,
  "hint": "use docs_search with a specific query to retrieve only relevant chunks"
}
```

The agent reads this hint and adapts its strategy — this is the C5 pattern of
*structured truncation*, not silent data loss.

---

## Step 6 — Embeddings (`core/embeddings.py`)

```python
_model: SentenceTransformer | None = None
_lock = threading.Lock()

def _get_model() -> SentenceTransformer:
    if _model is not None:
        return _model
    with _lock:
        if _model is None:   # double-checked locking
            _model = SentenceTransformer(settings.embedding_model)
    return _model
```

The double-checked locking pattern avoids the race condition where two threads
simultaneously see `_model is None` and both try to load the model. The first
thread acquires the lock, loads the model, and releases. The second thread
acquires the lock, sees `_model is not None`, and exits without loading again.

**Why `get_embedding_dim()` exists:**  
When `ensure_collection()` creates the Qdrant collection, it must specify the
vector size. Hardcoding `384` would break silently if someone changes
`EMBEDDING_MODEL` to a model with a different dimension. `get_embedding_dim()`
asks the model itself, so the collection always matches.

---

## Step 7 — Chunking (`core/chunking.py`)

```python
def chunk_text(text, chunk_size=500, overlap=50) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap   # slide window back by overlap
```

**Overlap** (50 words default) means consecutive chunks share 50 words at their
boundary. Without overlap, a sentence that straddles a chunk boundary would be
split — the first half in chunk N, the second half in chunk N+1, retrievable
by neither query. Overlap prevents this by including the tail of chunk N at the
top of chunk N+1.

**Word-based** chunking is chosen over character-based because word counts track
loosely with token counts across English text. A chunk of 500 words is roughly
500–700 tokens (depending on the model's tokenizer), which is predictable.
Character-based chunking could put a URL-heavy chunk at 200 tokens or a
lorem-ipsum chunk at 800, making sizes erratic.

---

## Common questions

**Q: Why is there a REST layer at all? The agent uses MCP.**  
The REST endpoints are a debugging affordance. During development you can:

```bash
curl -H "Authorization: Bearer tok_alice" http://localhost:8000/api/corpus/stats
```

This lets you inspect state without running the full agent. The REST and MCP
surfaces share the same `state.*` functions, so they always show the same data.

**Q: What happens if two orgs ingest a document with the same title?**  
Nothing bad. `document_id` is a fresh UUID per ingest — `title` is just a label.
Two orgs can have identically-titled documents with different content; the
`org_id` filter ensures they never see each other.

**Q: Why is the Qdrant client lazy-initialised in `_qc()` instead of at module load?**  
Module load happens at import time, before the FastAPI lifespan event runs. If
`QdrantClient(url=...)` were at module level, a bad `QDRANT_URL` would crash at
import, with a confusing traceback. Lazy init defers the connection attempt to
first use, which happens during the lifespan event — a clearly labelled startup
phase with a clear error message.

**Q: What's the difference between `docs_search` and `docs_get`?**  
`docs_search` does vector similarity search — you give it a natural-language query
and it returns the top-k most relevant *chunks*. `docs_get` fetches a *whole
document* by ID. The agent typically searches first, gets chunk IDs, and only
calls `docs_get` if it needs more context than the chunk snippets provide.
