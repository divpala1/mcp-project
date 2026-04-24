"""
LangGraph ReAct agent — the assembled runtime.

── API note (2026 migration) ─────────────────────────────────────────────────
`langgraph.prebuilt.create_react_agent` is deprecated. Its successor is
`langchain.agents.create_agent` (LangChain 1.x). Despite the module path,
the function still returns a LangGraph `CompiledStateGraph` — so we stay
100% on LangGraph primitives, which is the whole point of this project's
multi-agent trajectory (CLAUDE.md C3). The migration is a renaming and
a richer extension-point model, not a framework change.

Key differences vs `create_react_agent`:
    prompt=…                →  system_prompt=…
    pre_model_hook / post…  →  middleware=[…]  (see below)
    returns CompiledStateGraph (unchanged)

── ReAct loop ────────────────────────────────────────────────────────────────
The compiled graph implements the classic two-node loop:

    call_model   LLM sees messages + tool schemas; decides (a) reply to
                 the user or (b) emit one-or-more tool_calls.
    tools        ToolNode executes each tool_call (in parallel when possible)
                 and appends results as ToolMessages.
    conditional  If the last model message has tool_calls → loop to `tools`
                 → back to `call_model`. Otherwise → END.

── Extension points (no code here — comments mark where they'd live) ─────────

# NOTE(planning) — learning-checkpoint #5:
#   Subclass AgentMiddleware with a `before_model` hook that decomposes
#   the user request into a plan and seeds messages before the first
#   LLM call. Pass via `middleware=[MyPlanner()]`.
#
# NOTE(reflection):
#   AgentMiddleware with an `after_model` hook that inspects the model
#   response and decides whether to re-prompt. Same middleware list.
#
# NOTE(multi-agent — C3):
#   `create_agent` returns a CompiledStateGraph. To wrap this in a
#   supervisor graph, import `build_agent` in the supervisor module,
#   then `supervisor_graph.add_node("researcher", this_agent)` where
#   `this_agent` is our compiled graph. No rewrite needed. Pass
#   `name="researcher"` to create_agent so the parent graph can
#   identify it in traces.
#
# NOTE(memory):
#   `create_agent` accepts `checkpointer=` (langgraph `BaseCheckpointSaver`).
#   Pass `MemorySaver()` for in-memory dev, `PostgresSaver` etc. for prod.
#   That persists message history across runs. Semantic-recall memory
#   (retrieve relevant past turns from a vector store) is a middleware
#   `before_model` hook that prepends retrieved messages.
#
# NOTE(shipped-middleware inspiration): langchain.agents.middleware exposes
#   HumanInTheLoopMiddleware (human-in-the-loop — CLAUDE.md TODO(future)),
#   SummarizationMiddleware (context-window management),
#   LLMToolSelectorMiddleware (tool retrieval — CLAUDE.md C2 TODO(future)),
#   ToolCallLimitMiddleware / ModelCallLimitMiddleware (guardrails).
#   Useful to know exists; don't pull any in yet.
"""
from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph


SYSTEM_PROMPT = """You are a helpful research assistant.

You have tools in two namespaces:

  docs_*   — a document corpus scoped to the caller's organisation
             docs_ingest, docs_search, docs_list, docs_get, docs_stats

  notes_*  — a personal notes workspace for the caller's organisation
             notes_create, notes_list

Rules:
  1. If the user asks you to record, save, or remember something, use notes_create.
  2. For questions about corpus contents, call docs_search before answering.
     Do not fabricate content.
  3. When a tool returns an error (e.g. {"error": "not_found"}), describe the
     error to the user and suggest a next step rather than retrying blindly.
  4. Prefer small, targeted calls: top_k=3-5 for docs_search, limit=20 for docs_list.
"""


def build_agent(
    llm: BaseChatModel, tools: list[BaseTool],
) -> CompiledStateGraph:
    """
    Compile the ReAct graph. Returns a LangGraph `CompiledStateGraph` that
    the caller runs via `.astream_events(...)` for token-level streaming.

    `name="mcp-researcher"` labels this graph — when it's embedded as a
    sub-graph of a future supervisor, the name appears in traces and in
    LangSmith spans, which makes multi-agent runs readable.
    """
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        name="mcp-researcher",
    )
