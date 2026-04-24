# Notes Server Walkthrough

The notes server (`notes_server/server.py`) is the smallest possible second MCP
server. Its purpose is not to be a useful notes application — it's to prove that
`MultiServerMCPClient` can aggregate tools from multiple independent MCP servers
and that tool namespacing keeps those tools distinct.

Everything in this file is one page long by design. Read it alongside
`notes_server/server.py`.

---

## Why this server exists

When the agent connects to both servers via `MultiServerMCPClient`, the combined
tool list it sees is:

```
docs_ingest   docs_search   docs_list   docs_get   docs_stats   ← RAG server
notes_create  notes_list                                         ← Notes server
```

Without a second server, you could not observe:
- That `MultiServerMCPClient` really does merge tools from multiple origins.
- That tool namespacing (`docs_*` vs `notes_*`) prevents collisions.
- That the agent can route a "save a note" instruction to the right server
  transparently — it just calls `notes_create`, unaware that this goes to
  a different process on a different port.

---

## Why it's self-contained (no imports from `mcp_server/`)

The notes server deliberately does not import `mcp_server.auth` or
`mcp_server.core.config`, even though the auth logic is identical.

**The rule is: an MCP server should be deployable independently.** If the
notes server imported from `mcp_server`, you'd have to install and run both
packages together. Keeping it self-contained means:

- You can start `notes_server` without `mcp_server` even being present.
- Its dependency surface is easy to read in one file.
- The ~40 lines of duplicated auth is the explicit, accepted price of
  deployment independence.

The duplication is intentional, not an oversight.

---

## How requests flow through it

The structure mirrors the RAG server exactly, just simpler:

```
Agent (HTTP client)
  │
  │  GET /mcp/sse  Authorization: Bearer tok_alice
  ▼
auth_middleware
  │  look up token in auth_tokens dict (same AUTH_TOKENS_JSON as RAG server)
  │  set current_identity ContextVar to {"user_id": "alice", "org_id": "acme"}
  ▼
FastMCP SSE handler
  │  (later) tools/call  notes_create  {text: "searched for qubit today"}
  ▼
notes_create tool
  │  require_identity() → org_id = "acme"
  │  asyncio.to_thread(_create, "acme", text)
  ▼
_create()
  │  _notes["acme"].append({id: uuid, text: ..., created_at: ...})
  ▼
JSON result → MCP response → SSE → agent
```

---

## Storage — why in-memory is fine here

```python
_notes: dict[str, list[dict]] = {}
```

Notes are stored in a plain Python dict, keyed by `org_id`. They are wiped
when the process restarts.

This is acceptable because the server's job is to demonstrate the multi-server
pattern, not to be a real notes service. The C1 tenant isolation property still
holds: `_notes["acme"]` and `_notes["globex"]` are separate lists, and the
`org_id` key is always drawn from the authenticated ContextVar — never from the
request body.

For a real notes service, you'd swap the in-memory dict for a database write.
The tool signatures and auth layer would not change.

---

## Auth — same pattern as the RAG server

`ContextVar`, `auth_middleware`, and `require_identity()` are copied verbatim
from `mcp_server/auth.py`. The pattern is exactly the same:

1. Middleware validates the bearer token before routing.
2. Identity is stored in a `ContextVar` for the duration of the request.
3. Tool implementations call `require_identity()` to read it.

The token map (`AUTH_TOKENS_JSON`) is the same `.env` variable that the RAG
server reads. A token valid against the RAG server is automatically valid here.
This is the correct model: auth is a deployment-level concern (one token map,
one identity scheme), not something each server re-invents.

---

## MCP tools

```python
@mcp.tool()
async def notes_create(text: str) -> dict:
    """Create a note in the calling org's workspace."""
    org_id = require_identity()["org_id"]
    return await asyncio.to_thread(_create, org_id, text)

@mcp.tool()
async def notes_list() -> list[dict]:
    """List the calling org's notes, most recent first."""
    org_id = require_identity()["org_id"]
    return await asyncio.to_thread(_list, org_id)
```

These are the two simplest possible MCP tools:

- `notes_create` takes one argument, writes one record, returns it.
- `notes_list` takes no arguments, returns all notes for the caller's org.

`notes_list` returns most-recent-first because an LLM asked "what did I do
recently" benefits from seeing the latest entries at the top of its context
window rather than having to scan to the end.

`asyncio.to_thread` is used even here — `_create` and `_list` are sync
functions, and good hygiene means never calling sync code directly from an
async handler.

---

## Port 8001

The notes server listens on `127.0.0.1:8001` while the RAG server is on `8000`.
The agent's `config.py` (`NOTES_MCP_URL`) points to this port. There's nothing
special about 8001 — it just needs to not collide with 8000.

In a production deployment you'd put both servers behind a reverse proxy (nginx,
Caddy) and expose them on named subdomains or paths rather than port numbers.

---

## What this server teaches that the RAG server doesn't

| Concept | Where it shows up |
|---------|--------------------|
| Multi-server aggregation | `MultiServerMCPClient` in `agent/tools.py` merges both |
| Tool namespace isolation | `notes_*` vs `docs_*` — no collision, no glue code |
| Deployment independence | Self-contained auth, no cross-server imports |
| In-memory vs durable state | Contrast with Qdrant in the RAG server |
| Minimal MCP server | The smallest useful server is ~200 lines including REST debug routes |

---

## Common questions

**Q: Why is there a REST layer on this server too?**  
Same reason as the RAG server: curl-able endpoints for debugging during
development without needing to run the full agent.

```bash
curl -H "Authorization: Bearer tok_alice" http://localhost:8001/api/notes
```

**Q: What happens to notes when the server restarts?**  
They're gone. The in-memory `_notes` dict is wiped on every process start.
This is expected for a demo server. If you want persistence, replace the dict
with a SQLite write (two lines with Python's built-in `sqlite3` module) or any
other database.

**Q: Can the agent create a note and then search for it?**  
Not via similarity search — the notes server has no embedding or search tool.
`notes_list` returns everything for the org. If you added `notes_search`, you'd
need an embedding store (the RAG server's design), at which point you'd probably
just use `docs_ingest` for notes too. The current split keeps the demo scope clear.

**Q: How does the agent know to use `notes_create` for "save a note" vs `docs_ingest`?**  
The system prompt in `agent/agent.py` explicitly instructs:

> "If the user asks you to record, save, or remember something, use notes_create."

Without that instruction, the LLM would have to infer the difference from the
tool descriptions alone, which is less reliable. This is an example of
*prompt engineering as routing logic* — the system prompt is part of the
agent's control flow.
