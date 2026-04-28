# Prompt Registry Walkthrough

This document explains `agent/prompts/` — the registry that loads, versions, and
renders prompt templates at runtime. Read it alongside
[`agent/prompts/__init__.py`](__init__.py) and [`agent/prompts/system.md`](system.md).

---

## Why prompts live in files

The alternative — Python string constants — has a few problems in practice:

1. **Diffs are unreadable.** A changed sentence buried in a multiline Python
   string shows up in `git diff` as a string-constant change, not as the
   natural-language change it actually is. Reviewers have to parse escape
   sequences to see what the model will read.

2. **Iterating prompts means touching Python files.** When a product or research
   person wants to tune the system prompt, they shouldn't need to open a `.py`
   file and worry about indentation or escaping.

3. **No audit trail for prompt revisions.** With a plain string constant, there's
   no lightweight way to ask "which version of the prompt produced this run?".
   With a versioned file, the `version:` integer in the frontmatter answers that
   question, and every LangSmith trace is tagged with it.

---

## Directory layout

```
agent/prompts/
├── __init__.py      Prompt registry — the only Python file here
├── system.md        System prompt template (v2)
├── WALKTHROUGH.md   This file
└── archive/         (Retired prompts — kept for reference, not loaded)
```

`__init__.py` is where all registry logic lives. Prompt files are plain Markdown
with a thin YAML frontmatter block at the top.

---

## Frontmatter format

Every prompt file opens with:

```
---
version: N
---
```

Rules:
- `version` must be a positive integer.
- A missing `version:` field is a startup error — not a silent default. This
  prevents partially-edited files from silently running with an unknown version.
- Bump the integer on any meaningful change to the prompt body. There is no
  automatic enforcement of "meaningful"; the convention is: if the change alters
  what the model will do, bump it.
- The rest of the frontmatter is ignored for now (reserved for future fields like
  `model:` or `temperature:`).

Frontmatter is parsed by hand in `_parse_frontmatter()` — about 10 lines.
The field set is small and fixed; pulling in PyYAML for this would add more
dependency than value.

---

## The registry API

Four public functions are exported from `agent/prompts/__init__.py`:

### `get_prompt(name, /, **variables) → str`

Load the named prompt, render it with variable substitution, and return the
finished string.

```python
system_prompt = get_prompt(
    "system",
    tool_catalog=render_tool_catalog(tools),
)
```

- `name` is the filename stem: `"system"` → `agent/prompts/system.md`.
- `**variables` fills `{placeholder}` slots in the template body.
- Backed by `PromptTemplate.from_template` from `langchain-core` (already
  a transitive dependency — no new package).
- Raises `KeyError` if the file does not exist; raises with a clear message
  if a `{placeholder}` has no matching keyword argument.
- Literal `{` and `}` in the prompt body must be doubled (`{{`, `}}`).
  The system prompt currently avoids this by describing JSON shapes in prose
  rather than literal examples.

### `get_prompt_version(name) → str`

Return the version label for a prompt, e.g. `"v2"`.

```python
run_config = {
    "metadata": {
        "prompt_version": f"system@{get_prompt_version('system')}",
    },
}
```

Used by `agent/core.py` to tag every LangSmith trace with the active prompt
revision. In LangSmith you can group and filter runs by this metadata field,
which makes A/B comparison between prompt revisions straightforward.

### `bust_cache(name=None) → None`

Force the cache entry for `name` to be dropped. The next `_load` call will
re-read from disk regardless of mtime or TTL. Pass no argument to clear all
entries.

```python
from agent.prompts import bust_cache

bust_cache("system")   # bust one prompt
bust_cache()           # bust everything
```

Intended for test fixtures and admin scripts, not normal agent flow.

### `render_tool_catalog(tools) → str`

Build a human-readable, namespace-grouped tool catalog from the live tool list.

```python
render_tool_catalog(tools)
# Returns something like:
#   docs_*   — namespace
#              docs_get, docs_ingest, docs_list, docs_search, docs_stats
#
#   notes_*  — namespace
#              notes_create, notes_list
```

**Why derive this from live tools, not hardcode it?**

The catalog the LLM sees in its system prompt must match the tools actually
available for the current run. If you hardcode the catalog:

- Adding a new `@mcp.tool()` on the server requires a corresponding agent-side
  edit — two places to keep in sync.
- Different MCP server configurations (e.g. per-user server sets in production)
  would produce a wrong catalog for most callers.

Deriving it from `tools` (which were just fetched from the live MCP servers)
means the catalog cannot drift from reality.

Tools without an underscore in their name are grouped under `misc_*`.

---

## How it hooks into `core.py`

The connection happens at the start of `run_agent()`, right after tool
composition and before agent compilation:

```python
# agent/core.py (simplified)
tools, notools_reason = await compile_tools(            # step 4
    mcp_servers=servers,
    auth_token=auth_token,
)

system_prompt = get_prompt(                             # step 5
    "system",
    tool_catalog=render_tool_catalog(tools),
)
agent = build_agent(llm, tools, system_prompt=system_prompt)  # step 6
```

`compile_tools` (in [`agent/toolset.py`](../toolset.py)) merges MCP-loaded
tools with locally-registered ones from [`agent/registry.py`](../registry.py)
and is the seam where a future tool-finder layer would slot in.

`build_agent` in `agent/agent.py` passes `system_prompt` straight through to
`create_agent(system_prompt=...)`. The graph builder is prompt-agnostic — it
doesn't know or care where the string came from.

This separation means:

- Swapping the prompt (even to a dynamically-fetched one from MCP) requires
  only touching `core.py` at step 6.
- `build_agent` stays testable in isolation by passing any string for
  `system_prompt`.

---

## Caching

`_load(name)` uses a manual TTL + mtime cache (a plain `dict[str, _CacheEntry]`
protected by a `threading.Lock`). A cache entry is considered stale when **either**
condition is true:

1. **The file's mtime changed** — detected by comparing `path.stat().st_mtime` to
   the mtime recorded at load time. On every request (not on a background thread).
   This means edits take effect on the *next agent run* — no restart needed.

2. **The TTL has elapsed** — `PROMPT_CACHE_TTL_SECONDS` (default 30 s) since the
   last load. A safety net for editors or save tools that preserve mtime on write.

**Development workflow:** save `system.md`, run the agent again — it picks up the
change immediately because the mtime changed.

**Explicit invalidation:** call `bust_cache()` (no arguments) to clear all entries,
or `bust_cache("system")` to clear a single prompt. Useful in test fixtures that
need a guaranteed fresh read.

**Thread safety:** the lock ensures that two async tasks calling `_load` at the same
time for the same stale entry read the file once and share the result, rather than
both doing a disk read and racing on the cache dict write.

---

## `system.md` — section by section

```
---
version: 2
---
```
Frontmatter. Bump `version` on any meaningful edit.

```
You are a capable AI assistant. You complete tasks by reasoning step by step
and calling tools when they help.
```
Role preamble. Intentionally brief — the sections below do the heavy lifting.

```
# Tools available this session
{tool_catalog}
```
The `{tool_catalog}` placeholder is filled at runtime. The comment above it
tells the model that its tools are discovered dynamically and may change.

```
# Choosing a tool
```
Behavioural guidance for tool selection: match intent to description, use
namespace prefixes to scan, say "no tool fits" rather than inventing one.

```
# Using tools well
```
Tactical guidance: small targeted calls, modest limits, paginate rather than
dump, pass only declared arguments.

```
# Handling tool output
```
Error handling guidance: explain structured errors in plain language, handle
truncation/pagination signals explicitly, never fabricate content.

```
# Authorization
```
One important note: the model's authenticated session already scopes data to the
calling org at the server side. The model does not need to inject `user_id` or
`org_id` into tool arguments — that would be both redundant and potentially
unsafe (the server ignores it, but it clutters tool calls and confuses traces).

```
# When in doubt
```
Ask one clarifying question rather than guessing. Cheap compared to a wrong
action.

---

## How to add a new prompt

1. Create `agent/prompts/<name>.md` with a `version: 1` frontmatter block and
   any template body you want (use `{var}` for placeholders).

2. Call it from wherever it's needed:

   ```python
   from agent.prompts import get_prompt, get_prompt_version

   rendered = get_prompt("name", var=value)
   version  = get_prompt_version("name")   # "v1"
   ```

3. If the prompt goes into `build_agent` or `core.py`, pass its version to
   `run_config["metadata"]` alongside the system prompt version.

No changes to `__init__.py` are needed — `_load()` discovers files by name.

---

## How to add a new placeholder to `system.md`

1. Add `{my_var}` at the appropriate place in `system.md`.
2. Bump the `version:` integer.
3. Pass `my_var=...` in the `get_prompt("system", ...)` call in `core.py`.

If you forget step 3, `PromptTemplate.format()` raises a `KeyError` at the call
site — an immediate, clear error rather than a silent wrong prompt.

---

## Future: MCP `prompts` capability

The MCP spec defines a `prompts` capability that allows servers to advertise
named prompt templates. When this lands in `langchain-mcp-adapters`, the registry
can grow a second source:

```python
# TODO(future): agent/prompts/__init__.py
# _load() can consult MCP first (via MultiServerMCPClient.get_prompts()),
# merge remote and local templates into the same name → (meta, body) dict,
# and fall back to local files for names not found remotely. The public
# API (get_prompt, get_prompt_version) stays the same.
```

The public API (`get_prompt`, `get_prompt_version`) does not need to change —
callers are isolated from the source.

---

## Common questions

**Q: What if I accidentally omit the `version:` field?**
`_load()` raises `ValueError` immediately with a message pointing to the file
and explaining exactly what's missing. The process won't start.

**Q: Can I use multi-line or complex YAML in the frontmatter?**
The parser only handles `key: value` lines (no nesting, no lists, no quoting).
For anything more complex, add `python-frontmatter` or `PyYAML` as a dependency.
For now the field set is intentionally minimal.

**Q: Why `PromptTemplate` and not an f-string?**
Two reasons. First, `PromptTemplate` raises a clear error on missing variables
rather than silently leaving `{var}` in the output or crashing with a confusing
`KeyError`. Second, it's a LangChain primitive already pulled in transitively —
no new dependency.

**Q: Can two prompts share a variable?**
Yes — `get_prompt` renders each template independently. Shared variables are
just passed as keyword arguments to each `get_prompt` call.

**Q: Why not store prompts in the database / a remote registry?**
For a learning project, files are the right default: zero infrastructure,
readable in any editor, versioned by git. A remote registry becomes interesting
when you want non-engineer stakeholders to edit prompts without a code deploy.
The `TODO(future)` comment in `__init__.py` marks where that would slot in.
