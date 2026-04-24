# Agent Walkthrough

This document explains `main.py` step by step, and how it connects to every other
file in the `agent/` package. Read it alongside the source — each section maps to
a concrete line or block you can find in the code.

---

## The big picture

When you run:

```bash
python -m agent.main "Search the corpus for qubit entanglement"
```

Six things happen in order:

```
1. Config validation      agent/config.py       read .env, crash-fast if anything's missing
2. Tracing setup          agent/observability.py wire LangSmith if key is present
3. LLM construction       agent/llm.py           instantiate the right provider (Groq / Anthropic / Ollama)
4. MCP tool loading       agent/tools.py         connect to both MCP servers, get their tool lists
5. Agent compilation      agent/agent.py         bind tools to LLM, build the LangGraph graph
6. Streaming run          agent/main.py          push the prompt, print events as they arrive
```

The sections below walk each step in detail.

---

## Step 1 — Config validation (`agent/config.py`)

`config.py` is imported the moment any other `agent.*` module is imported.
`AgentConfig` is a [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
class — it reads `.env` on construction and raises a `ValidationError` immediately if
a required value is missing or the wrong type.

**Why this matters for learners:**  
Failing fast at startup is far less confusing than seeing a cryptic `KeyError` or
`AttributeError` somewhere in the middle of an async tool call three layers deep.
This is the "validate at the boundary" principle applied to configuration.

`settings` (the singleton) is a module-level variable — every other file imports it
and the class is only constructed once.

---

## Step 2 — Tracing setup (`agent/observability.py`)

```python
setup_tracing()
```

This is a no-op if `LANGSMITH_API_KEY` is not in `.env`. If it is, LangSmith
tracing activates for every LangChain object created after this point.

**Why this must run first:**  
LangChain's LangSmith client reads its env vars once, at import time of
`langchain_core`. Calling `setup_tracing()` before `get_llm()` / `build_agent()`
ensures those vars are set before any tracing-sensitive object is constructed.
Swap the order and you get a silent miss — the agent runs but nothing is traced.

---

## Step 3 — LLM construction (`agent/llm.py`)

```python
llm = get_llm()
```

`get_llm()` reads `LLM_PROVIDER` and `LLM_MODEL` from `settings` and returns a
`BaseChatModel`. The rest of the codebase never sees `ChatGroq` or `ChatAnthropic` —
only the abstract base type. This is the single change point for swapping providers
(learning checkpoint C4).

**Why lazy imports?**  
Each provider SDK (groq, anthropic, ollama) pulls in its own HTTP transport and
auth dependencies. Importing all three at module level would slow startup and require
all three to be installed even when only one is used. The `if provider == "groq": from
langchain_groq import ChatGroq` pattern defers the import to the branch actually taken.

---

## Step 4 — MCP tool loading (`agent/tools.py`)

```python
client = build_mcp_client()
tools = await load_tools(client)
```

This is the most important step to understand if you're new to MCP.

### What `build_mcp_client()` does

It creates a `MultiServerMCPClient` configured for two servers:

| Server name | URL                           | What it exposes          |
|-------------|-------------------------------|--------------------------|
| `rag`       | `http://127.0.0.1:8000/mcp/sse` | `docs_*` tools (Qdrant RAG) |
| `notes`     | `http://127.0.0.1:8001/mcp/sse` | `notes_*` tools (in-memory) |

The bearer token (`settings.agent_auth_token`) is placed in the `headers` dict.
This header is sent on every SSE connection — which, in langchain-mcp-adapters 0.2.x,
means it's sent on every individual tool invocation.

### What `load_tools(client)` does

`client.get_tools()` connects to each server, performs the MCP handshake, and
retrieves the tool list in JSON Schema format. `langchain-mcp-adapters` then converts
each MCP tool into a LangChain `BaseTool` with:

- `.name` → MCP tool name (e.g. `docs_search`)
- `.description` → MCP tool description
- `.args_schema` → pydantic model generated from the JSON Schema

This conversion is **learning checkpoint #3**: MCP JSON Schema → LangChain BaseTool.
After this point, the MCP-ness is invisible — the agent sees ordinary LangChain tools.

### Why the two calls are separate

`build_mcp_client()` is sync and cheap — it just stores the server config. `load_tools()`
is async because it actually opens network connections. Keeping them separate makes
both easier to test (you can construct the client without hitting the network) and
makes the `await` explicit and visible.

---

## Step 5 — Agent compilation (`agent/agent.py`)

```python
agent = build_agent(llm, tools)
```

`build_agent` calls `create_agent(model=llm, tools=tools, ...)` and returns a
`CompiledStateGraph`. Internally, this compiles the classic two-node ReAct loop:

```
     ┌──────────────────────────────────────────┐
     │                                          │
    ──→ call_model ── tool_calls? ──→  tools  ──┘
                   ── no tool calls ──→  END
```

**`call_model` node:**  
Sends the current message list (plus all tool schemas) to the LLM. The LLM replies
with either:
- plain text → graph ends, that text is the answer
- one or more `tool_calls` (structured JSON with tool name + arguments) → continue

**`tools` node (ToolNode):**  
Receives the tool calls, executes them (in parallel when possible), and appends the
results as `ToolMessage` objects to the message list. Then loops back to `call_model`.

**`llm.bind_tools(tools)` (learning checkpoint #4):**  
`create_agent` calls this internally. It serializes every tool's JSON Schema and
appends it to the API request as a `tools` array. The LLM uses these schemas to
know what names and argument shapes it can invoke. Without `bind_tools`, the LLM
can talk about tools but can't actually call them.

---

## Step 6 — Streaming run (`agent/main.py`)

```python
async for event in agent.astream_events(
    {"messages": [{"role": "user", "content": prompt}]},
    version="v2",
):
```

`astream_events` runs the LangGraph graph and yields events as they happen —
not after the full run finishes. This is learning checkpoint #6.

### The input

`{"messages": [...]}` is the initial state. `MessagesState` (LangGraph's built-in
state type) expects a `messages` key. Each ReAct iteration appends to this list:
user message → AI message (with tool_calls) → ToolMessages → AI message → … → END.

### Events you'll see

| Event name             | When it fires                                | What we do with it            |
|------------------------|----------------------------------------------|-------------------------------|
| `on_chat_model_stream` | One per token as the LLM generates           | Print the token immediately   |
| `on_tool_start`        | Right before a tool is invoked               | Print `⚙  tool_name(args)`    |
| `on_tool_end`          | After the tool returns                       | Print `→ result`              |
| `on_chat_model_start`  | LLM call starting (ignored here)            | —                             |
| `on_chat_model_end`    | Full LLM message assembled (ignored here)   | —                             |
| `on_chain_start/end`   | Graph node boundaries (ignored here)        | —                             |

We only handle three events because that's all the user-facing output needs. In a
production UI, `on_chain_start` with the node name would drive a "thinking…" spinner,
and `on_chat_model_end` would signal that a paragraph is fully rendered.

### The `in_text` flag

```python
in_text = False

# inside the loop:
if kind == "on_chat_model_stream":
    if not in_text:
        print("🤖 ", end="", flush=True)
        in_text = True
    print(text, end="", flush=True)
elif kind == "on_tool_start":
    if in_text:
        print()          # finish the current text line
        in_text = False
```

This is a tiny state machine with two states: *currently streaming text* vs. *not*.
Without it, a tool-call event mid-stream would print `⚙  docs_search(...)` on the
same line as a half-finished sentence. The flag lets us close the text line cleanly
before printing the tool badge.

### Why `flush=True`?

`print(text, end="", flush=True)` writes immediately to stdout instead of waiting for
a newline to trigger the buffer flush. Without it, you'd see no output until the LLM
finishes an entire response — exactly the opposite of streaming.

### Content block normalisation

```python
text = chunk.content if isinstance(chunk.content, str) else "".join(
    b.get("text", "") for b in chunk.content if isinstance(b, dict)
)
```

Groq and most providers return `chunk.content` as a plain string. Anthropic returns
a list of content blocks like `[{"type": "text", "text": "Hello"}]`. This one-liner
handles both shapes so the provider swap (C4) requires no change here.

---

## How the files relate — a dependency map

```
main.py
  ├── observability.py    (setup_tracing)
  ├── llm.py              (get_llm)  ──→  config.py
  ├── tools.py            (build_mcp_client, load_tools)  ──→  config.py
  └── agent.py            (build_agent)
          └── uses llm + tools from above
```

`config.py` is the only file that touches `.env`. Everything else receives values
through `settings` (singleton) or through function arguments. This makes each module
independently testable: pass a fake LLM and fake tools to `build_agent`, and it
assembles a graph without any network or API calls.

---

## Common questions

**Q: What if an MCP server is down when I run the agent?**  
`load_tools()` will raise a connection error. The agent won't start. This is
intentional — a partially-wired agent that silently has fewer tools than expected
is harder to debug than a startup failure.

**Q: Can I add a third MCP server?**  
Yes. In `tools.py`, add a third entry to the dict passed to `MultiServerMCPClient`.
Namespacing (the `tool_*` prefix convention) is what prevents name collisions — make
sure the new server's tools have a unique prefix.

**Q: Why not just `agent.invoke(...)` instead of `agent.astream_events(...)`?**  
`invoke` waits for the entire run to finish before returning anything. For a
conversational agent, that means the user stares at a blank screen for 10–30 seconds.
`astream_events` lets you render tokens as they arrive, which is the UX that users
actually expect from an LLM-backed tool.

**Q: Where does memory go?**  
Short-term memory is already here: the `messages` list in state accumulates the full
conversation. Long-term (cross-session) memory would extend `MessagesState` with a
`user_id` / `session_id`, then add a `before_model` middleware that fetches relevant
past turns from a vector store. The extension point is marked with
`# NOTE(memory):` in `agent.py`.

**Q: How do I switch from Groq to Ollama?**  
In `.env`, set `LLM_PROVIDER=ollama` and `LLM_MODEL=llama3.2` (or whatever model
you've pulled). Nothing else changes — `get_llm()` in `llm.py` reads these at
runtime and returns the right `BaseChatModel`. The rest of the code never sees the
provider name.
