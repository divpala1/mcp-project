"""
Prompt registry — loads prompt templates from agent/prompts/*.md and renders
them with runtime context.

Why prompts live in their own files (not as Python constants):
  - Edit prompt text without touching Python code. Diffs are clean — prompt
    changes show up as natural-language diffs, which is what reviewers want
    to see for prompt iterations.
  - The same registry shape grows trivially when planning / reflection
    prompts arrive (the `# NOTE(planning)` and `# NOTE(reflection)` markers
    in `agent/agent.py`).

Why `PromptTemplate.from_template`:
  - It's a LangChain primitive already pulled in via `langchain-core` (a
    transitive dependency of `langchain.agents`). No new package.
  - Same `{var}` syntax users encounter everywhere else in LangChain.
  - Strict at render time: missing variables raise immediately with a clear
    error (CLAUDE.md "fail fast at startup"). Caveat: literal `{` and `}`
    must be doubled (`{{`, `}}`). We avoid the issue by rewording the
    system prompt's JSON-error example in prose.
  - Returns a raw string. (Note: `ChatPromptTemplate` looks similar but
    `.format()` returns a chat-message-list serialization with `Human:`
    role prefixes — not what we want when we hand the result to
    `create_agent(system_prompt=...)` as a plain string.)

Why this lives in `__init__.py` (not a sibling `prompts.py` module):
  - A file `agent/prompts.py` and a directory `agent/prompts/` cannot
    coexist cleanly — Python's import system silently picks the package
    and shadows the module file. Putting the registry code in the
    package's `__init__.py` gives us one name (`agent.prompts`) with
    code and prompt files under one roof. `Path(__file__).parent` then
    naturally resolves to the prompt directory.

Versioning:
  - Each `.md` opens with a tiny YAML frontmatter block declaring an
    integer `version`. Author bumps the integer on any meaningful edit.
  - `get_prompt_version(name)` returns `"v{n}"` for use as trace metadata.
    Callers (see `agent/core.py`) pass it into `RunnableConfig.metadata`
    so every LangSmith span records which prompt revision produced it.
  - Frontmatter is parsed by hand (~10 lines below) — the field set is
    small and fixed; pulling in `python-frontmatter` or PyYAML for this
    would be more dependency than value.
  - Missing `version:` is a startup error, not a silent default. A prompt
    without a version is a sign of an incomplete edit, not a state to
    tolerate.

# TODO(future): when MCP `prompts` capability lands, the registry can grow
# a second source — fetch via `MultiServerMCPClient.get_prompts()` and
# merge into the same name -> (meta, body) dict. The render API
# (`get_prompt`, `get_prompt_version`) stays the same; only `_load`
# learns to consult MCP first and fall back to local files.
"""
from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Iterable

from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool

PROMPTS_DIR = Path(__file__).parent

__all__ = ["get_prompt", "get_prompt_version", "render_tool_catalog"]


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """
    Strip a leading `---\\n…\\n---\\n` block and parse it as `key: value` lines.

    Returns (meta, body). If no frontmatter block is present, returns
    `({}, text)` — the caller validates that required fields exist.

    Deliberately tiny: no nested structures, no lists, no quoting rules.
    Anything more elaborate and we should pull in PyYAML.
    """
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body


@cache
def _load(name: str) -> tuple[dict[str, str], str]:
    """
    Read `agent/prompts/{name}.md`, parse frontmatter, return (meta, body).

    Cached because prompt files are static during a process's lifetime. To
    pick up edits, restart the process — same as how config env vars work.
    """
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise KeyError(f"Prompt {name!r} not found at {path}")
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    if "version" not in meta:
        # Fail fast: the version is part of the prompt's contract. Missing
        # means an incomplete edit, not a default-to-something situation.
        raise ValueError(
            f"Prompt {name!r} at {path} is missing a `version:` field in "
            f"its frontmatter. Add a `---\\nversion: N\\n---` block at the top."
        )
    return meta, body


def get_prompt(name: str, /, **variables: object) -> str:
    """
    Render the named prompt with the given variables.

    Args:
        name: filename stem under `agent/prompts/` (e.g. "system" → system.md).
        **variables: substitutions for `{placeholders}` in the template body.

    Raises:
        KeyError: prompt file not found.
        ValueError: prompt file missing a `version:` frontmatter field.
        KeyError (from PromptTemplate): a `{placeholder}` in the body
            had no matching keyword argument.
    """
    _meta, body = _load(name)
    return PromptTemplate.from_template(body).format(**variables)


def get_prompt_version(name: str) -> str:
    """
    Return the version label for a prompt (e.g. `"v1"`).

    Used by `agent/core.py` to tag LangSmith trace metadata with the active
    prompt revision so every run can be correlated to the exact prompt
    body that produced it.
    """
    meta, _body = _load(name)
    return f"v{meta['version']}"


def render_tool_catalog(tools: Iterable[BaseTool]) -> str:
    """
    Build a human-readable, namespace-grouped tool catalog.

    Output shape (matches the format the system prompt previously hand-typed):

        docs_*   — namespace
                 docs_get, docs_ingest, docs_list, docs_search, docs_stats

        notes_*  — namespace
                 notes_create, notes_list

    Why this is templated rather than hand-typed: the catalog is now derived
    from the tools the agent actually loaded over MCP. Adding a new tool to
    a server (e.g. another `@mcp.tool()`) automatically updates what the
    LLM sees in its system prompt — the prompt cannot drift from reality.

    Tools without an underscore in their name are grouped under `misc_*`.
    """
    groups: dict[str, list[str]] = {}
    for tool in tools:
        prefix = tool.name.split("_", 1)[0] if "_" in tool.name else "misc"
        groups.setdefault(prefix, []).append(tool.name)

    lines: list[str] = []
    for prefix in sorted(groups):
        names = sorted(groups[prefix])
        lines.append(f"  {prefix}_*   — namespace")
        lines.append(f"             {', '.join(names)}")
        lines.append("")
    return "\n".join(lines).rstrip()
