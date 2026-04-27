## Who I Am

I am an AI engineer with hands-on experience building RAG pipelines, agentic workflows,
and integrating AI into software projects. I have recently started learning MCP and want
to understand how to build production-grade AI agents that connect to MCP servers.
I am comfortable with Python and have previously written agent loops from scratch.

**The goal of this project is learning by doing.** Every architectural and code decision
should be explainable. If you make a non-obvious choice, leave a brief comment or note
explaining *why*, not just *what*.

---

## Mental Model: What a Modern AI Agent Actually Is

Tool calling is the *mechanism* modern agents use to interact with the world, but an
agent in production is more than a tool-calling loop. It is composed of:

1. **The reasoning loop** — ReAct (reason → act → observe → repeat) is the atom.
2. **Tool calling** — the interface between the LLM and everything else (APIs, DBs, MCP).
3. **Memory** — short-term (conversation messages) and long-term (vector-backed recall
   across sessions). Not every agent needs both.
4. **Planning** — either emergent (the LLM plans inside ReAct) or explicit
   (plan-then-execute, where a planning step produces a list of sub-tasks).
5. **State management** — explicit, inspectable state is what makes an agent debuggable
   and what enables human-in-the-loop. This is why LangGraph uses a state graph.
6. **Control flow** — loops, conditional branches, parallel sub-agents, interrupts.
7. **Reflection / self-critique** — the agent evaluates its own output and retries or
   refines. Often a second LLM call with a critique prompt.
8. **Observability** — tracing (LangSmith, OpenTelemetry), evaluations, feedback loops.
   Without this, you cannot improve an agent in production.

This project directly touches 1, 2, 3, 5, 6, and 8. Points 4 and 7 will be called out
in comments where they would naturally slot in, so I understand *where* they belong
even if we don't implement them now.

---

## Project Goals

1. **Understand MCP deeply** — resources, tools, prompts, SSE transport, session lifecycle, and authorization. Understand how a custom agent connects to an MCP server vs. how Claude Desktop does it.
2. **Build a production-grade AI agent** — not a toy script. Structured the way a real engineering team would build and maintain it.
3. **Keep scope moderate but extensible** — start with a general-purpose ReAct agent connected to one (then two) MCP servers. The architecture must support growing into multi-agent, memory-enabled systems without a rewrite.

---

## Calibration — Questions I've Been Wondering About

These are doubts I've been sitting with. They give you a sense of the depth of engagement I want. They are not a checklist — they are the floor, not the ceiling. Whenever you hit a decision point with similar weight, treat it the same way, regardless of whether it appears below.

### C1 — Per-user / per-org document access

The MCP server must scope resources to the calling user/organization. A user from Org A must not be able to search or see documents from Org B, even if they call the same tool.

**How we'll implement it:**
- The agent sends a bearer token in the `Authorization` header when connecting to the
  MCP SSE endpoint.
- A FastAPI dependency validates the token and resolves it to a `{user_id, org_id}`.
- A `contextvars.ContextVar` holds the current request's identity, accessible to MCP
  tool implementations without changing their signatures.
- Every Qdrant query is filtered by `org_id` via Qdrant's payload filters.
- A comment in the tool code explicitly notes: *"MCP itself has no concept of users —
  auth is a transport-layer concern."* We use bearer tokens for simplicity; the MCP
  spec's OAuth 2.1 flow is the production-grade equivalent and should be noted as
  `# TODO(future)`.

### C2 — Tool explosion and multiple MCP servers

**(a) Too many tools on one server.** LLMs degrade when given 20–30+ tools — they confuse similar tools, hallucinate arguments, or pick the wrong one. Address it with:
- **Tool namespacing:** prefix tools by domain (`docs_search`, `docs_ingest`,
  `notes_create`). Names become self-documenting.
- **Tool filtering per task:** at agent init, optionally pass a subset of tools based
  on task type. Demonstrate via a simple config flag.
- **Note (don't implement) tool retrieval:** embed tool descriptions, retrieve the
  top-k relevant tools for the user query, expose only those to the LLM. Leave a
  `# TODO(future)` with a sketch of where it would plug in.

**(b) Multiple MCP servers.** `MultiServerMCPClient` accepts a dict of named servers and aggregates their tools. We will:
- Run the main RAG MCP server (`rag-server`).
- Run a second, smaller MCP server (`notes-server`, 2–3 tools) to prove the pattern.
- Show that namespacing keeps tool names distinct.

### C3 — Multi-agent readiness

We are not building a multi-agent system now, but the project must not paint itself
into a corner:
- Agent is a LangGraph graph, not a monolithic function.
- State is explicit (`MessagesState` to start; easy to extend).
- LLM, tools, and graph are assembled in separate files — independently testable and
  reusable.
- When we add a supervisor agent later, it will import the current agent as a
  sub-graph (idiomatic LangGraph).
- A `# NOTE(multi-agent):` comment in `agent.py` will mark the exact extension point.

### C4 — Easy LLM provider switching

A single environment variable switches the LLM:
- `agent/llm.py` exposes `get_llm()` which reads `LLM_PROVIDER` + `LLM_MODEL` from
  config and returns a `BaseChatModel`.
- Supported from day one: `groq`, `anthropic`, `ollama`. OpenAI trivial to add.
- **Start with Groq** (`langchain-groq`). Fast inference, good tool calling on Llama
  models, ideal for iterative learning.
- The rest of the code never imports a specific provider — it only sees `BaseChatModel`.

### C5 — How agents handle huge data

The honest answer: **agents never load huge data into context.** They operate on
summaries, metadata, and retrieved slices. The project will demonstrate these patterns
in the MCP server's tool design:

- **Retrieval, not loading.** `search_documents` returns top-k chunks with scores and
  source IDs, never the whole corpus.
- **Hierarchical tools.** `list_documents(limit, cursor)` and `get_document(id)` are
  separate tools. The agent navigates instead of dumping.
- **Pagination.** List tools return `{items, next_cursor, total}`. The agent decides
  whether to keep paging.
- **Response size caps.** Every tool wrapper enforces a max response size (e.g. 8 KB).
  If truncated, the response includes `"truncated": true` and a hint on how to narrow
  the query. The LLM sees this and adapts.
- **Metadata-first tools.** `describe_corpus` returns stats and schema, not content.
  The agent uses this to decide what to retrieve.
- **Structured queries when appropriate.** Note (don't implement): for truly large
  structured data, the right pattern is giving the agent a SQL-execution tool rather
  than streaming rows through the LLM.

Every tool we write should include a comment on which of these patterns it uses.

### C6 — Observability

Production agents are unusable without traces:
- Integrate **LangSmith** tracing, optional via `LANGSMITH_API_KEY`. Agent runs fine
  without it.
- Structured logging via `logging` with a consistent format.
- A `# NOTE(observability):` comment in `main.py` marks where evals would plug in.

---

## Tech Stack

### Agent Framework — LangGraph
Explicit graph-based agents. LLM-agnostic. Scales to multi-agent without rewrites.
Do not use LangChain's legacy `AgentExecutor`.

### MCP Integration — langchain-mcp-adapters
Converts MCP tools to LangChain tools. Handles SSE session, JSON-RPC, schema mapping.
Use `MultiServerMCPClient` so multi-server support is in from day one (even with one
server at first).

### LLM — Groq first, pluggable
- Start with **Groq** (`langchain-groq`), default `llama-3.3-70b-versatile` (good tool
  calling, fast).
- Swappable to Anthropic, Ollama, etc. via env vars only.

### Vector DB — Qdrant
- Use **Qdrant** in local/Docker mode (no cloud account needed).
- Qdrant's payload filtering implements per-org access control (C1). This is a teaching
  point — use payload filters (not separate collections per org) for the main demo,
  and note in a comment when you'd pick collection-per-tenant instead (compliance,
  scale, noisy neighbors).

### Embeddings — sentence-transformers
`all-MiniLM-L6-v2`, local, no API key. Swappable later.

### MCP Server — FastAPI + FastMCP
Keep the existing pattern: one FastAPI process exposing both REST (`/api/*`) and MCP
SSE (`/mcp/sse`). Both layers share `core/state.py`. The existing `server.py` is the
right shape — replace dummy logic with real Qdrant-backed logic and add auth.

### Python Environment
- Python 3.11+
- `pip` for dependency management
- `python-dotenv` + `pydantic-settings` for config
- Secrets only in `.env`

---

## MCP Server — What to Build

Turn the existing RAG scaffold into a real, org-scoped RAG server.

**Real functionality:**
- **Ingest documents** — chunk, embed, store in Qdrant with `org_id` in payload.
- **Search documents** — embed query, similarity search filtered by the calling org's
  `org_id`, return top-k chunks with source metadata.
- **List documents** — paginated, org-scoped.
- **Corpus stats** — real counts from Qdrant, scoped to the calling org.

**Auth:**
- Bearer token in `Authorization` header.
- Dev-mode token-to-identity map in `.env` (e.g.
  `AUTH_TOKENS_JSON={"tok_alice":{"user_id":"alice","org_id":"acme"},"tok_bob":{"user_id":"bob","org_id":"globex"}}`).
- Identity carried via `contextvars.ContextVar`.

**Chunking:** fixed-size with overlap. Simple. Note semantic chunking as future.

**Second MCP server (demonstrates multi-server):**
- Tiny `notes_server` with `create_note(text)` and `list_notes()`.
- In-memory storage is fine. Point is to show `MultiServerMCPClient` aggregating tools.

---

## Agent Architecture

### Structure

```
agent/
├── __init__.py        # Public API: run_agent, AgentEvent, McpServerSpec
├── agent.py           # LangGraph graph via create_agent(). Marks extension points
│                      # for planning, reflection, memory, and multi-agent (C3).
├── core.py            # Framework-free run_agent() engine — the seam CLI, FastAPI,
│                      # and tests all call. Yields AgentEvent dicts.
├── tools.py           # MCP tool loading via MultiServerMCPClient. Handles session
│                      # lifecycle and auth header injection.
├── llm.py             # get_llm() factory. Reads LLM_PROVIDER + LLM_MODEL from config.
├── config.py          # pydantic-settings. All env vars validated at startup.
├── observability.py   # LangSmith / logging setup.
├── api.py             # Optional FastAPI APIRouter (POST /agent/chat, SSE streaming).
│                      # Drop into any host with include_router(); or import run_agent
│                      # directly for a custom endpoint.
├── app.py             # 3-line standalone FastAPI host. For local testing.
├── main.py            # CLI entrypoint. Reads AGENT_AUTH_TOKEN, renders events to
│                      # stdout with emoji markers.
└── prompts/
    ├── __init__.py    # Prompt registry: get_prompt(), get_prompt_version(),
    │                  # render_tool_catalog(). Loads *.md files on first use,
    │                  # caches per-process.
    └── system.md      # System prompt template (v2). Contains {tool_catalog}
                       # placeholder filled at runtime from the live MCP tool list.
```

### Agent Loop

Use `create_agent` from `langchain.agents` (successor to the deprecated `create_react_agent`):
1. `call_model` — LLM decides to respond or call tools.
2. `tools` (`ToolNode`) — executes tool calls.
3. Conditional edge — loop back if tool calls, end if not.

Document in a comment where you would replace `create_react_agent` with a hand-built
graph and why (custom routing, pre/post hooks, planning node, reflection node).

### MCP Session Lifecycle (critical learning point)

Unlike Claude Desktop (which manages the session transparently), a custom agent
manages it explicitly. This deserves a clear comment block in `tools.py` and `main.py`:

```python
# MCP session lifecycle:
# 1. MultiServerMCPClient opens an SSE connection to each configured server.
# 2. On connection, it performs the MCP handshake (initialize -> tools/list).
# 3. Tools are returned as LangChain BaseTool objects, ready to bind to the LLM.
# 4. The session must remain open for the duration of agent execution — tool calls
#    flow over this same SSE connection.
# 5. On exit, the session is cleanly torn down.
#
# This is why the agent runs INSIDE the `async with client:` block, not before or
# after. Forgetting this is the most common mistake when moving from Claude Desktop
# to a custom agent.
```

The auth bearer token is injected via `MultiServerMCPClient`'s per-server `headers`
config. Show this in code.

### State

Start with `MessagesState`. Do not design a custom state schema until needed. When we
add long-term memory, we'll extend state with `user_id` and `session_id` — leave a
comment marking this.

### Streaming

Wire up `graph.astream_events` from day one. Stream model tokens to stdout as they
arrive. No batch-only responses — that is not production behaviour.

---

## Code Style & Principles

**Simplicity first.** No abstractions until needed. One clear function beats three
polymorphic classes.

**Explainability over cleverness.** A verbose, clearly-named implementation with a
one-line "why" comment is always preferred over a terse clever one. Optimize for my
future-self understanding.

**Robustness, not over-engineering.**
- `pydantic-settings` validates config at startup. Missing env var → fail fast.
- Every tool call that can fail wraps errors and returns a structured error message
  to the agent. The agent should *see* the error and adapt, not crash.
- Use `logging`. No print statements except user-facing output in `main.py`.

**No premature optimization.** Sync Qdrant calls inside async routes via
`asyncio.to_thread` are fine. No pooling/caching/batching until measured.

**Type hints everywhere.** `from __future__ import annotations`. Pydantic models for
anything crossing a boundary.

---

## Project Layout

```
project-root/
├── CLAUDE.md
├── NOTES.md                   # Running log of learning checkpoints (Claude Code fills in)
├── README.md
├── test_agent.py              # End-to-end smoke test for POST /agent/chat SSE endpoint
├── .env
├── .env.example
├── pyproject.toml
├── docker-compose.yml         # Qdrant container
│
├── mcp_server/
│   ├── server.py              # FastAPI + FastMCP entrypoint
│   ├── auth.py                # Bearer token → identity via ContextVar
│   ├── WALKTHROUGH.md         # File-by-file walkthrough with single-request trace
│   └── core/
│       ├── config.py          # pydantic-settings, fail-fast validation
│       ├── state.py           # Qdrant-backed RAG engine, org-scoped
│       ├── embeddings.py      # sentence-transformers singleton
│       └── chunking.py        # Fixed-size word chunker with overlap
│
├── notes_server/              # Second MCP server (demonstrates multi-server pattern)
│   ├── server.py
│   └── WALKTHROUGH.md         # Why it exists, auth, in-memory storage, tool design
│
└── agent/
    ├── __init__.py            # Public API: run_agent, AgentEvent, McpServerSpec
    ├── agent.py               # LangGraph graph builder
    ├── core.py                # Framework-free run_agent() engine
    ├── tools.py               # MCP client builder, session lifecycle, auth
    ├── llm.py                 # get_llm() factory (groq | anthropic | ollama)
    ├── config.py              # pydantic-settings, default_mcp_servers()
    ├── observability.py       # Optional LangSmith tracing
    ├── api.py                 # Optional FastAPI APIRouter (POST /agent/chat, SSE)
    ├── app.py                 # 3-line standalone host for local testing
    ├── main.py                # CLI entrypoint
    ├── WALKTHROUGH.md         # Layer-by-layer guide through the agent package
    └── prompts/
        ├── __init__.py        # Prompt registry (get_prompt, get_prompt_version,
        │                      # render_tool_catalog)
        ├── system.md          # System prompt template (v2) with {tool_catalog}
        └── WALKTHROUGH.md     # Prompt registry walkthrough
```

---

## Environment Variables

```
# .env.example

# LLM
LLM_PROVIDER=groq              # groq | anthropic | ollama
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434

# MCP Servers
RAG_MCP_URL=http://127.0.0.1:8000/mcp/sse
NOTES_MCP_URL=http://127.0.0.1:8001/mcp/sse
AGENT_AUTH_TOKEN=tok_alice     # Token the agent uses to authenticate to MCP

# MCP Server (auth)
AUTH_TOKENS_JSON={"tok_alice":{"user_id":"alice","org_id":"acme"},"tok_bob":{"user_id":"bob","org_id":"globex"}}

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=documents

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Observability (optional)
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=mcp-agent-learning
```

---

## Key Learning Checkpoints

As code is written, surface these concepts in comments or `NOTES.md`:

1. **MCP session lifecycle** (in `tools.py` + `main.py`).
2. **Auth as a transport concern** (in `mcp_server/auth.py`) — MCP has no native user
   concept; bearer token → identity via contextvars.
3. **Tool schema conversion** — how MCP's JSON Schema becomes LangChain `BaseTool`s
   via `langchain-mcp-adapters`.
4. **LLM tool binding** — what `llm.bind_tools(tools)` does in the API request.
5. **ReAct loop in LangGraph** — how `create_react_agent` wires the nodes, where
   you'd customize.
6. **Streaming** — `astream_events` structure, `on_chat_model_stream` events.
7. **Multi-server aggregation** — how `MultiServerMCPClient` merges tool lists and
   why namespacing matters.
8. **Org-scoped retrieval** — Qdrant payload filters in action.
9. **Huge-data patterns (C5)** — called out at each tool using pagination, retrieval,
   or truncation.
10. **LLM provider swap** — demonstrate switching Groq → Ollama with only env vars.
11. **Where memory goes** — mark the state extension point.
12. **Where a supervisor would wrap this agent** — mark the multi-agent extension point.

---

## What NOT to Build (Yet)

Mark any occurrence as `# TODO(future): ...`:
- Long-term / vector-backed agent memory
- Multi-agent supervisor
- Human-in-the-loop interrupts
- Tool retrieval (embedding-based tool selection)
- OAuth 2.1 flow (bearer tokens are sufficient for now)
- Semantic chunking
- Reflection / self-critique loops
- Evaluation harness
- Frontend / UI
- Production-grade rate limiting, retries with backoff beyond basic cases

---

## How to Run (Target State)

```bash
# 1. Start Qdrant
docker compose up -d

# 2. Start the RAG MCP server
uvicorn mcp_server.server:app --host 127.0.0.1 --port 8000

# 3. Start the notes MCP server (demonstrates multi-server)
uvicorn notes_server.server:app --host 127.0.0.1 --port 8001

# 4. Run the agent
python -m agent.main "Ingest this doc titled 'Quantum Computing': ... Then search for qubit entanglement. Also, add a note saying I did this search today."
```

The agent should:
- Connect to both MCP servers over SSE with a bearer token.
- Discover tools from both (namespaced).
- Ingest the document (scoped to its org).
- Search the corpus (only finding this org's docs).
- Create a note in the notes server.
- Stream its response token-by-token.