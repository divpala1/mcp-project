# Agent Walkthrough

This document explains how the `agent/` package is wired and how the pieces fit
together. Read it alongside the source — each section maps to a concrete file or
block you can find in the code.

The agent has two visible entry points (CLI and FastAPI) and one shared engine
underneath. Most of the interesting logic lives in the engine; the entry points
are thin renderers over the same event stream.

---

## The big picture

```
┌──────────────────────────────────────────────┐
│  agent/main.py    ◄── CLI:   `python -m agent.main "..."`
│                       reads AGENT_AUTH_TOKEN, prints emoji-decorated stream
├──────────────────────────────────────────────┤
│  agent/api.py     ◄── FastAPI router:  POST /agent/chat
│  agent/app.py         3-line standalone host (uvicorn agent.app:app)
│                       reads `Authorization: Bearer ...` header, streams SSE
├──────────────────────────────────────────────┤
│  agent/core.py     ◄── run_agent(prompt, *, auth_token, mcp_servers=None)
│                       framework-free async generator yielding AgentEvent dicts
├──────────────────────────────────────────────┤
│  agent/agent.py    build_agent(llm, tools, system_prompt) → CompiledStateGraph
│  agent/llm.py      get_llm() factory (memoized)
│  agent/toolset.py  compile_tools(mcp_servers, auth_token) → (tools, reason)
│  agent/tools.py    build_mcp_client(servers, *, auth_token), load_tools(client)
│  agent/registry.py local tool registry: register(tool) / registered_tools()
│  agent/prompts/   get_prompt("system", tool_catalog=...) + render_tool_catalog(tools)
│  agent/config.py   pydantic-settings + default_mcp_servers() helper
│  agent/observability.py   optional LangSmith
└──────────────────────────────────────────────┘
```

When you invoke the agent — through either the CLI or HTTP — six things happen
inside `run_agent()`:

```
1. Tracing setup        agent/observability.py      enable LangSmith if key is present
2. LLM construction     agent/llm.py                instantiate the right provider (cached)
3. Server resolution    agent/config.py             env defaults OR caller's `mcp_servers=`
4. Tool composition     agent/toolset.py            merge MCP-loaded tools + local registry
5. Prompt rendering     agent/prompts/__init__.py   fill {tool_catalog} from live tool list
6. Agent compilation    agent/agent.py              bind tools to LLM, build the LangGraph graph
```

After step 5, `run_agent()` iterates `astream_events` from the graph and
translates LangGraph's heterogeneous event stream into a small, stable
`AgentEvent` shape. Whichever entry point invoked it (CLI / FastAPI) iterates
those events and renders them.

The sections below walk through each layer.

---

## Layer 1 — Configuration (`agent/config.py`)

`config.py` is imported the moment any other `agent.*` module is imported.
`AgentConfig` is a [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
class — it reads `.env` on construction and raises a `ValidationError`
immediately if a required value is missing or the wrong type.

**What lives here:**
- `LLM_PROVIDER`, `LLM_MODEL`, provider API keys
- `RAG_MCP_URL`, `NOTES_MCP_URL` — defaults for the local demo MCP servers
- `GITHUB_MCP_URL`, `GITHUB_PAT` — optional GitHub hosted MCP (static PAT credential)
- `LANGCHAIN_DOCS_MCP_URL` — optional LangChain Docs hosted MCP (public, no auth)
- `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`
- `thinking_budget_tokens` — Anthropic-only; max internal reasoning tokens when thinking mode is enabled

**What does NOT live here (anymore):**
- The bearer token used to talk to MCP. That's a per-request value now —
  forwarded from the caller's `Authorization` header in the FastAPI path,
  read from the `AGENT_AUTH_TOKEN` env var by the CLI itself.

### `default_mcp_servers()`

A small helper that assembles the env-driven default server set:

```python
def default_mcp_servers() -> dict[str, McpServerSpec]:
    mcp_servers: dict[str, McpServerSpec] = {}

    if settings.rag_mcp_url:
        mcp_servers["rag"] = {"url": settings.rag_mcp_url, "transport": "sse"}

    if settings.notes_mcp_url:
        mcp_servers["notes"] = {"url": settings.notes_mcp_url, "transport": "sse"}

    # GitHub only joins when a PAT is configured — omitting it avoids surfacing
    # auth failures inside the agent loop for users who haven't set up a PAT.
    if settings.github_pat:
        mcp_servers["github"] = {
            "url": settings.github_mcp_url,
            "transport": "streamable_http",
            "static_token": settings.github_pat,   # service credential, not user token
        }

    # LangChain Docs: public, no auth, streamable_http.
    if settings.langchain_docs_mcp_url:
        mcp_servers["langchain_docs"] = {
            "url": settings.langchain_docs_mcp_url,
            "transport": "streamable_http",
        }

    return mcp_servers
```

This is the *only* place the server names appear hard-coded — everywhere else
operates on a generic `dict[str, McpServerSpec]`. That's deliberate: production
hosts that want per-user / per-org MCP-server resolution skip this helper entirely
and pass their own dict to `run_agent()`.

**Two auth models side by side.** `rag` and `notes` use the per-request user token
(no `static_token` — `build_mcp_client` injects the caller's bearer). `github` uses
`static_token`: a PAT the agent holds in env, used as the bearer for that server
regardless of who the human caller is. `langchain_docs` has no auth at all — the
server ignores any header it receives. All three patterns co-exist without changing
`build_mcp_client`; it just checks whether `static_token` is present to decide which
credential to inject.

**Why this matters for learners:**
Failing fast at startup is far less confusing than seeing a cryptic `KeyError`
or `AttributeError` somewhere in the middle of an async tool call three layers
deep. This is the "validate at the boundary" principle applied to
configuration.

---

## Layer 2 — The engine (`agent/core.py`)

`core.py` is the seam every host calls. It knows nothing about HTTP, SSE, argv,
or stdout.

```python
async def run_agent(
    prompt: str,
    *,
    auth_token: str,
    mcp_servers: dict[str, McpServerSpec] | None = None,
) -> AsyncIterator[AgentEvent]:
    ...
```

Three inputs, one output type. Inputs split cleanly between "what the user is
asking" (`prompt`, `auth_token`) and "where this deployment talks to"
(`mcp_servers`, optional). Output is an async iterator of small typed dicts.

### Step 1 — Tracing setup (`agent/observability.py`)

```python
setup_tracing()
```

No-op if `LANGSMITH_API_KEY` is unset. If set, LangSmith tracing activates for
every LangChain object created after this point.

**Why this must run first:** LangChain's LangSmith client reads its env vars at
import time of `langchain_core`. Calling `setup_tracing()` before `get_llm()`
ensures those vars are set before any tracing-sensitive object is constructed.
Swap the order and you get a silent miss — the agent runs but nothing is
traced.

### Step 2 — LLM construction (`agent/llm.py`)

```python
llm = get_llm()  # memoized
```

`get_llm()` reads `LLM_PROVIDER` and `LLM_MODEL` from `settings` and returns a
`BaseChatModel`. The rest of the codebase never sees `ChatGroq` or
`ChatAnthropic` — only the abstract base type. This is the single change point
for swapping providers (learning checkpoint C4).

**Why `@lru_cache(maxsize=1)`?** The LLM client has no per-user state and is
safe to share across requests/threads. Memoizing gives every FastAPI request
the same instance for free, without needing `lifespan` plumbing or `app.state`
juggling. The CLI hits the same cache (it just uses it once).

**Why lazy imports per provider?** Each provider SDK (groq, anthropic, ollama)
pulls in its own HTTP transport and auth dependencies. Importing all three at
module level would slow startup and require all three to be installed even
when only one is used. The `if provider == "groq": from langchain_groq import
ChatGroq` pattern defers the import to the branch actually taken.

### Step 3 — Server resolution

```python
servers = mcp_servers if mcp_servers is not None else default_mcp_servers()
```

If the caller passed an `mcp_servers` dict (e.g. the production FastAPI app
resolved a per-user set), use that. Otherwise fall back to the env defaults.
This is the "hybrid config" pattern: env-backed default + per-request
override, because *which MCP servers does this user have access to?* is going
to be a per-user question in production but is a deployment-wide constant in
the dev demo.

### Step 4 — Tool composition (`agent/toolset.py`)

```python
tools, notools_reason = await compile_tools(
    mcp_servers=servers,
    auth_token=auth_token,
)
```

`compile_tools` is the single seam responsible for producing the final
tool list the agent binds to. It pulls from two sources and never raises
— failures are mapped to `notools_reason`, a short string the no-tool
system prompt surfaces back to the LLM so the model can explain the
situation rather than crashing the stream.

**Source A — MCP servers ([`agent/tools.py`](tools.py)).** When `servers`
is non-empty, `compile_tools` calls:

```python
client = build_mcp_client(servers, auth_token=auth_token)
mcp_tools = await load_tools(client)
```

`build_mcp_client` injects the bearer token (or, for servers with a
`static_token`, that service credential) into per-server headers. The
header is sent on every SSE connection — which, in
`langchain-mcp-adapters` 0.2.x, means it's sent on every individual tool
invocation.

`client.get_tools()` connects to each server, performs the MCP handshake,
and retrieves the tool list in JSON Schema format.
`langchain-mcp-adapters` then converts each MCP tool into a LangChain
`BaseTool` with:

- `.name` → MCP tool name (e.g. `docs_search`)
- `.description` → MCP tool description
- `.args_schema` → pydantic model generated from the JSON Schema

This conversion is **learning checkpoint #3**: MCP JSON Schema → LangChain
`BaseTool`. After this point, the MCP-ness is invisible — the agent sees
ordinary LangChain tools.

If `load_tools` raises (server unreachable, bad handshake), the exception
is logged with traceback and `mcp_error` is set; the agent keeps any
locally-registered tools and runs with whatever's left.

**Source B — local registry ([`agent/tools/registry.py`](tools/registry.py)).** Hand-written
Python tools register at import time:

```python
from langchain_core.tools import tool
from agent.tools import register

@register
@tool
def get_current_time() -> str:
    """Return the current UTC time."""
    ...
```

`compile_tools` calls `registered_tools()` and concatenates the result
onto the MCP list. Local tools are useful for things that don't need to
live behind an MCP server — date/time helpers, format converters,
in-process calculations.

**Why a per-request `build_mcp_client`?** Headers are baked into
`MultiServerMCPClient` at construction time in the 0.2.x adapter, and
the bearer token is a per-request value. So we build a fresh client per
call — that's fine, construction is cheap (no network I/O until the
first tool call).

**Future seam — the tool-finder layer.** A `# NOTE` block in
`compile_tools` marks where embedding-based or LLM-based tool selection
would slot in (CLAUDE.md C2a). The shape would be `list[BaseTool] →
list[BaseTool]` (filter / rerank), so no caller changes when it lands.

### Step 5 — Prompt rendering (`agent/prompts/`)

```python
system_prompt = get_prompt(
    "system",
    tool_catalog=render_tool_catalog(tools),
)
```

`render_tool_catalog` groups the tools just loaded in Step 5 by namespace prefix
and formats them into a human-readable catalog string:

```
  docs_*   — namespace
             docs_get, docs_ingest, docs_list, docs_search, docs_stats

  notes_*  — namespace
             notes_create, notes_list
```

`get_prompt` reads `agent/prompts/system.md`, strips the YAML frontmatter, and
renders the template body with `{tool_catalog}` replaced by that string.

**Why derive the catalog from live tools, not hardcode it?** Adding a new
`@mcp.tool()` on the server side is all that's needed — the system prompt's tool
list stays in lockstep automatically. A hardcoded catalog drifts; a derived one
cannot.

**Prompt versioning:** `system.md` opens with a `---\nversion: N\n---` block.
`get_prompt_version("system")` returns `"v2"` (or whatever integer is there).
`core.py` passes this to LangGraph's `run_config`:

```python
run_config = {
    "metadata": {
        "prompt_version": f"system@{get_prompt_version('system')}",
    },
}
```

Every LangSmith span for this run is tagged with `system@v2`, so you can group
and compare runs across prompt revisions without guessing which text produced
which behaviour.

**Caching:** both `_load(name)` and the returned string are `@cache`-decorated —
the file is read once per process lifetime. To pick up edits: restart the process
(same as config env vars).

See [agent/prompts/WALKTHROUGH.md](prompts/WALKTHROUGH.md) for a full walkthrough
of the registry design.

---

### Step 6 — Agent compilation (`agent/agent.py`)

```python
agent = build_agent(llm, tools, system_prompt=system_prompt)
```

`build_agent` calls `create_agent(model=llm, tools=tools, ...)` and returns a
`CompiledStateGraph`. Internally, this compiles the classic two-node ReAct
loop:

```
     ┌──────────────────────────────────────────┐
     │                                          │
    ──→ call_model ── tool_calls? ──→  tools  ──┘
                   ── no tool calls ──→  END
```

**`call_model` node:** sends the current message list (plus all tool schemas)
to the LLM. The LLM replies with either plain text (graph ends, that text is
the answer) or one or more `tool_calls` (continue to the tools node).

**`tools` node (ToolNode):** receives the tool calls, executes them (in
parallel when possible), and appends the results as `ToolMessage` objects to
the message list. Then loops back to `call_model`.

**`llm.bind_tools(tools)` (learning checkpoint #4):** `create_agent` calls
this internally. It serialises every tool's JSON Schema and appends it to
the API request as a `tools` array. The LLM uses these schemas to know what
names and argument shapes it can invoke. Without `bind_tools`, the LLM can
talk about tools but can't actually call them.

### Step 7 — Streaming and event translation

```python
async for event in agent.astream_events(
    {"messages": [{"role": "user", "content": prompt}]},
    version="v2",
):
    ...  # translate to AgentEvent dicts and yield
```

`astream_events` runs the LangGraph graph and yields events as they happen —
not after the full run finishes. This is **learning checkpoint #6**.

LangGraph emits a wide variety of events; `core.run_agent` filters down to
the three that callers actually want to render and translates them into a
small, stable shape:

| LangGraph event           | Translated `AgentEvent`                              |
|---------------------------|------------------------------------------------------|
| `on_chat_model_stream`    | `{"type": "token", "text": "..."}`                   |
| `on_tool_start`           | `{"type": "tool_start", "name": "...", "args": {}}`  |
| `on_tool_end`             | `{"type": "tool_end", "name": "...", "output": ...}` |
| (everything else)         | (skipped)                                            |

Plus two terminal events `core.py` emits itself:

| `AgentEvent`                                      | When                                  |
|---------------------------------------------------|---------------------------------------|
| `{"type": "error", "message": "..."}`             | Anything raised during the run        |
| `{"type": "end"}`                                 | Always last (in `finally`)            |

**Why translate?** Two reasons. First, LangGraph's event names are tied to its
internal vocabulary (`on_chat_model_stream` is a LangChain-ism, not an
agent-ism). Translation keeps the public contract stable even if we swap the
underlying graph machinery later. Second, error handling: a raw async generator
that raises mid-stream is hard for FastAPI to recover from cleanly — by
yielding a terminal `error` event and a guaranteed `end`, the consumer always
sees a well-formed stream.

### Content-block normalisation

Hidden inside the `on_chat_model_stream` branch:

```python
text = chunk.content if isinstance(chunk.content, str) else "".join(
    b.get("text", "") for b in chunk.content if isinstance(b, dict)
)
```

Groq and most providers return `chunk.content` as a plain string. Anthropic
returns a list of content blocks like `[{"type": "text", "text": "Hello"}]`.
This one-liner handles both shapes, so the provider swap (C4) requires no
changes anywhere outside `llm.py`.

---

## Layer 3a — CLI rendering (`agent/main.py`)

`main.py` is a thin renderer over `run_agent()`:

```python
async def _print_stream(prompt: str, auth_token: str) -> None:
    in_text = False
    async for event in run_agent(prompt, auth_token=auth_token):
        kind = event["type"]
        if kind == "token":
            ...   # emoji prefix on first token, then print text chunks
        elif kind == "tool_start":
            ...   # print ⚙ tool_name(args)
        elif kind == "tool_end":
            ...   # print → result
        elif kind == "error":
            ...   # print to stderr
```

### The `in_text` flag

A tiny state machine with two states: *currently streaming text* vs. *not*.
Without it, a tool-call event mid-stream would print `⚙  docs_search(...)` on
the same line as a half-finished sentence. The flag lets us close the text
line cleanly before printing the tool badge.

### Why `flush=True`?

`print(text, end="", flush=True)` writes immediately to stdout instead of
waiting for a newline to trigger the buffer flush. Without it, you'd see no
output until the LLM finishes an entire response — exactly the opposite of
streaming.

### Auth token handling

```python
token = os.getenv("AGENT_AUTH_TOKEN")
if not token:
    sys.exit(...)
```

The CLI reads its bearer token from env. This is a developer convenience —
in production, the FastAPI endpoint forwards the user's actual `Authorization`
header instead, and `AGENT_AUTH_TOKEN` doesn't exist.

---

## Layer 3b — FastAPI rendering (`agent/api.py`, `agent/app.py`)

`api.py` exposes the same event stream, but as Server-Sent Events. The router
is *optional* — you only pay for it if you import `agent.api`.

### The endpoint

```python
@router.post("/chat")
async def chat(req: ChatRequest, authorization: str | None = Header(None)):
    token = _extract_bearer(authorization)
    return StreamingResponse(
        _sse_stream(req.prompt, token),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

`_extract_bearer` is a header-shape check, not a token validation — the agent
never inspects the token's contents. The MCP server (`mcp_server/auth.py`) is
the single source of truth on identity. We fail fast at the FastAPI layer
when the header is missing or malformed so we don't waste an LLM call on an
obviously bad request.

### The SSE encoding

```python
async def _sse_stream(prompt: str, auth_token: str):
    async for ev in run_agent(prompt, auth_token=auth_token):
        yield f"data: {json.dumps(ev, default=str)}\n\n"
```

Same `run_agent` call. Same iteration. Different rendering — each event
becomes one `data:` frame in the SSE stream. `default=str` shields us from
non-JSON-serialisable values (e.g. ToolMessage objects appearing in tool
outputs); they get stringified rather than crashing the stream.

### The standalone host (`agent/app.py`)

Three lines:

```python
from fastapi import FastAPI
from agent.api import router

app = FastAPI(title="Agent Service")
app.include_router(router)
```

Run with `uvicorn agent.app:app --port 8002`. Used here for end-to-end testing
without coupling the agent to the existing `mcp_server` FastAPI app (they're
conceptually different services — one is an MCP *server*, this is an MCP
*client*).

In production, the same two lines (`from agent.api import router` +
`include_router(router)`) drop into the host app's existing FastAPI instance.
Or — if the host needs custom auth, request shape, or per-user MCP-server
resolution — they import `from agent import run_agent` and write their own
endpoint. Both paths use the same `core.py` engine.

### Why SSE and not WebSockets?

LangGraph's `astream_events` is already a one-way async iterator; SSE is the
simplest streaming shape that maps onto it. Browsers + curl both consume it
without ceremony. WebSockets would add bidirectional capability (cancel,
mid-turn user input) we don't need yet — when per-conversation memory and
interactive cancellation land, WS becomes interesting.

---

## How the files relate — a dependency map

```
main.py               api.py
   │                     │
   └────────┬────────────┘
            │
         core.py  (run_agent, AgentEvent, McpServerSpec)
            │
   ┌────────┼─────────┬─────────────┬──────────┬──────────┐
   │        │         │             │          │          │
observability.py  llm.py       toolset.py    agent.py  prompts/
                    │            │     │       │
                    │       tools.py  registry.py
                    │            │
                    └────► config.py ◄────────┘
                              │
                            .env
```

`config.py` is the only file that touches `.env`. Everything else receives
values either through `settings` (the singleton) or through function
arguments. This makes each module independently testable: pass a fake LLM and
fake tools to `build_agent`, and it assembles a graph without any network or
API calls. Pass a fake `mcp_servers` dict + dummy auth token to `run_agent`,
and the engine runs against any test stub. `toolset.compile_tools` is itself
testable in isolation — feed it an empty server dict plus a registry seeded
via `agent.tools.register(...)` and assert on the merged list.

---

## Layer 4 — Prompt registry (`agent/prompts/`)

The prompt registry is a small, self-contained package that keeps prompt text out
of Python source files. Full details are in
[agent/prompts/WALKTHROUGH.md](prompts/WALKTHROUGH.md); the short version:

**Why a registry at all?** Two reasons:

1. *Diffs are readable.* Prompt changes show up in `git diff` as natural-language
   diffs, not string-constant diffs buried inside Python files. Reviewers see what
   the model will read, not an escaped multiline literal.

2. *Extensible without touching Python.* The registry is designed so that when
   planning and reflection prompts arrive, they are just more `.md` files. The
   registry API (`get_prompt`, `get_prompt_version`) doesn't change.

**Three public functions:**

| Function | What it does |
|---|---|
| `get_prompt(name, **vars)` | Load, cache, and render the named prompt with variable substitution |
| `get_prompt_version(name)` | Return `"vN"` from the frontmatter; used as LangSmith trace metadata |
| `render_tool_catalog(tools)` | Derive a namespace-grouped catalog string from the live tool list |

**The `system.md` structure** (read alongside the file):

```
---              ← YAML frontmatter
version: 2       ← bump this on any meaningful edit
---
You are a capable AI assistant...

# Tools available this session
{tool_catalog}   ← filled at runtime by render_tool_catalog(tools)

# Choosing a tool
...

# Using tools well
...

# Handling tool output
...

# Authorization
...

# When in doubt
...
```

The sections after the tool catalog are behavioural guardrails — they remain
constant across runs. The catalog is the only dynamic part; it varies by which MCP
servers are connected.

---

## Common questions

**Q: What if an MCP server is down when I run the agent?**
`load_tools()` raises a connection error. `compile_tools` (in
[`agent/toolset.py`](toolset.py)) catches it, logs the offending URL with
traceback, and returns an empty MCP list plus a `notools_reason`. The agent
still runs — it falls back to whatever tools are in the local registry, or to
the no-tool prompt that lets the LLM explain the situation to the user. The
stream always terminates cleanly with an `end` event.

**Q: How do I add a hand-written Python tool (no MCP server)?**
Use the registry in [`agent/tools/registry.py`](tools/registry.py):

```python
from langchain_core.tools import tool
from agent.tools import register

@register
@tool
def get_current_time() -> str:
    """Return the current UTC time."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
```

Tools register at import time. As long as the module containing the
`@register` call is imported before `run_agent()` runs (the typical hosts —
`agent/main.py`, `agent/app.py` — are good places to import them from), the
tool surfaces in the LLM's catalog alongside MCP-loaded ones. `compile_tools`
in [`agent/toolset.py`](toolset.py) handles the merge; you don't need to
touch `core.py`.

**Q: Can I add a third MCP server?**
Two ways. (1) Edit `default_mcp_servers()` in `config.py` to add a new entry — it'll
show up in every CLI run and FastAPI request. See the GitHub and LangChain Docs
entries already in there for the two patterns: `static_token` for a service
credential, or no `static_token` for a per-request user token. (2) Pass a custom
`mcp_servers` dict to `run_agent(...)` from your host endpoint — that overrides the
default and is how production multi-tenant resolution works. Namespacing (the
`<prefix>_<verb>` convention) is what prevents name collisions — make sure the new
server's tools have a unique prefix.

**Q: Why not just `agent.invoke(...)` instead of `agent.astream_events(...)`?**
`invoke` waits for the entire run to finish before returning anything. For a
conversational agent that means the user stares at a blank screen for 10–30
seconds. `astream_events` lets the engine emit token-level events as they
arrive, which is the UX users expect from an LLM-backed tool. The CLI prints
them; the FastAPI router streams them as SSE frames; both paths are live.

**Q: Where does memory go?**
Short-term memory is already here: the `messages` list in state accumulates
the full conversation *within a single `run_agent()` call*. Long-term
(cross-session) memory needs (a) a way for the host to identify a session
(`session_id` argument to `run_agent`), and (b) a checkpointer (`MemorySaver`
or `PostgresSaver`) passed through to `create_agent`. The extension point is
marked with `# NOTE(memory):` in `agent.py` and again in `core.py`.

**Q: How do I switch from Groq to Ollama?**
In `.env`, set `LLM_PROVIDER=ollama` and `LLM_MODEL=llama3.2` (or whatever
model you've pulled). Nothing else changes — `get_llm()` in `llm.py` reads
these and returns the right `BaseChatModel`. The rest of the code never sees
the provider name.

**Q: How does the FastAPI surface authenticate users in production?**
The router does the minimum: extract the bearer token from the
`Authorization` header and forward it verbatim to MCP. The MCP server is
the source of truth on identity (it validates the token and resolves it to
`{user_id, org_id}`). If you need richer auth (JWT, OAuth, your own session
table), don't mount the default router — write a custom endpoint that
pulls identity however you like and passes the appropriate `auth_token`
string to `run_agent()`.

**Q: Can the same FastAPI process host both the agent AND another service?**
Yes — that's the point of `agent.api` shipping as an `APIRouter` rather than
as a complete app. `app.include_router(router)` slots the agent's `/agent/*`
routes alongside whatever else your app exposes. `agent/app.py` is just a
demo wrapper for running the agent in isolation.
