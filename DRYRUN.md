# Dry Run — Request Flow

This document traces the execution path of a single agent request, from the API endpoint through response streaming. It assumes MCP servers are available and return tools successfully. If no MCP servers are present, or if they return no tools, the tool-related steps are skipped and a default system prompt is used instead.

---

## 1. `api.py` — Entry Point

1. The query string is passed to the `POST /agent/chat` endpoint.
2. The authorization token is extracted from the request.
3. `run_agent()` (defined in `core.py`) is called with the prompt, auth token, and enable-thinking parameter. It returns an async streaming response iterator.

---

## 2. `core.py` — Agent Initialization

4. `run_agent()` accepts the prompt, auth token, an optional enable-thinking flag, and an optional `mcp_servers` dictionary. It returns an `AsyncIterator` that yields response chunks as the agent produces them.
5. The LLM is initialized by calling `get_llm()`, which applies the enable-thinking parameter.
6. The `mcp_servers` value is resolved; if the caller did not pass one, `default_mcp_servers()` is used to build it from env (`RAG_MCP_URL`, `NOTES_MCP_URL`, `GITHUB_PAT`, `LANGCHAIN_DOCS_MCP_URL`).
7. `compile_tools(mcp_servers=..., auth_token=...)` (in [`agent/toolset.py`](agent/toolset.py)) is awaited. It is the single seam responsible for tool composition — the function never raises; failures are returned as a human-readable `notools_reason` string instead.

   Inside `compile_tools()`:

   - If the server dict is non-empty, `build_mcp_client()` is called with the auth token and `load_tools()` retrieves the MCP tool list (a list of LangChain `BaseTool` objects). A connection or handshake error is logged and turned into a `notools_reason`.
   - `registered_tools()` (from [`agent/registry.py`](agent/registry.py)) is appended — these are local Python tools registered via `@register`.
   - The merged list is returned. (A future tool-finder layer would slot in here, narrowing the list per query without touching any caller. CLAUDE.md C2a.)

8. If at least one tool is available, the system prompt with tool-usage instructions is fetched via `get_prompt("system")`, rendered with a formatted catalog string containing namespace-grouped tool names.
9. If no tools loaded, the no-tool prompt (`system_notools.md`) is fetched, with `notools_reason` substituted in so the LLM can explain the situation to the user.
10. The agent is initialized by calling `build_agent()` with the LLM, tools (possibly empty), and the resolved system prompt.
11. The streaming response is produced via `agent.astream_events()`, which yields chunks as they are generated.

> **Reference:** [`astream_events` API docs](https://reference.langchain.com/python/langchain-core/runnables/base/Runnable/astream_events)

---

## 3. `core.py` — Inside the Response Iterator

The iterator inspects each event by its type:

```python
kind = event.get("event")
```

The three event types handled are described below.

---

### `on_chat_model_stream`

Emitted for each token of text content produced by the LLM.

The chunk content is extracted:

```python
chunk = event["data"]["chunk"]
content = chunk.content
```

If the content is a dict, the `"text"` field is extracted and accumulated into a single string. The event is then yielded as:

```python
yield {"type": "token", "text": text}
```

---

### `on_tool_start`

Emitted when the agent begins executing a tool. Contains metadata about the tool being called.

The tool name and arguments are extracted and yielded:

```python
yield {
    "type": "tool_start",
    "name": event.get("name", "<tool>"),
    "args": event["data"].get("input", {}),
}
```

---

### `on_tool_end`

Emitted when a tool finishes execution. Contains metadata about the tool and its output.

The tool name and output are extracted and yielded:

```python
yield {
    "type": "tool_end",
    "name": event.get("name", "<tool>"),
    "output": event["data"].get("output"),
}
```

---

## 4. End of Stream

Once all events are exhausted, the iterator yields a final end marker:

```python
yield {"type": "end"}
```