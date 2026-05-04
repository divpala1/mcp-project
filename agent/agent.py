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
#
# Prompt content lives in `agent/prompts/` (markdown files + a small
# registry in `agent/prompts/__init__.py`). When MCP `prompts` capability
# is wired up, that registry is where it slots in — `build_agent` itself
# stays prompt-agnostic.
"""
from __future__ import annotations

import logging

from langchain.agents import create_agent
from langchain.agents.middleware import before_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import RemoveMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.graph.state import CompiledStateGraph

log = logging.getLogger(__name__)


def _make_trim_middleware(max_messages: int):
    """
    Build a @before_model middleware that trims the message history to at
    most `max_messages` entries before each LLM call.

    Why @before_model and not a post-processing step:
        The trim must happen *before* the LLM sees the messages so it never
        receives a context that exceeds the cap. Trimming after would still
        persist the full history to the checkpointer for the next turn.

    What gets kept:
        messages[0]               — always preserved as an anchor (typically
                                    the system prompt injected by create_agent,
                                    or the first HumanMessage if no system
                                    prompt is in state).
        messages[-max_messages:]  — the most recent `max_messages` messages.

    Why RemoveMessage(id=REMOVE_ALL_MESSAGES) + re-add:
        LangGraph's MessagesState uses an `add_messages` reducer — you can't
        just assign a new list. The REMOVE_ALL_MESSAGES sentinel tells the
        reducer to wipe the channel first; the messages that follow then
        become the new state. This is the canonical LangGraph trimming pattern.

    Note: max_messages counts individual message objects (HumanMessage,
    AIMessage, ToolMessage), not turns. A turn that calls two tools produces
    ~5 messages. Size your cap accordingly.
    """
    @before_model
    def _trim(state, runtime) -> dict | None:
        messages = state["messages"]
        if len(messages) <= max_messages:
            return None

        # Keep the anchor (messages[0]) + the most recent `max_messages`.
        # Deduplicate: if the anchor is already inside the recent slice
        # (i.e. total history is only slightly over the cap), don't add it
        # twice.
        recent = messages[-max_messages:]
        anchor = messages[0]
        kept = recent if anchor.id in {m.id for m in recent} else [anchor, *recent]

        log.debug(
            "trim_middleware: %d → %d messages (cap=%d)",
            len(messages), len(kept), max_messages,
        )
        return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *kept]}

    return _trim


def build_agent(
    llm: BaseChatModel,
    tools: list[BaseTool],
    *,
    system_prompt: str,
    checkpointer: BaseCheckpointSaver | None = None,
    max_messages: int | None = None,
) -> CompiledStateGraph:
    """
    Compile the ReAct graph. Returns a LangGraph `CompiledStateGraph` that
    the caller runs via `.astream_events(...)` for token-level streaming.

    `system_prompt` is rendered by the caller (`agent/core.py`) using the
    prompt registry — that's where runtime context like the discovered
    MCP tool list becomes available for substitution. Keeping rendering
    out of this function means the graph builder doesn't know or care
    where prompts come from.

    `checkpointer` is the LangGraph persistence layer (CLAUDE.md learning
    checkpoint #11). When provided, the compiled graph snapshots its state
    after every step, keyed by the `thread_id` the caller supplies in
    `config["configurable"]`. Subsequent runs with the same thread_id
    resume from the last snapshot — the LLM sees prior turns automatically,
    no caller-side message threading required. None means stateless mode
    (current default; no behavioural change for callers that don't opt in).

    `max_messages` caps the number of messages kept in the LangGraph state
    before each LLM call. When set, a `@before_model` trim middleware is
    injected automatically (see `_make_trim_middleware`). None = no trimming.
    Most useful when a checkpointer is also attached (history grows across
    turns), but applies within a single turn too if tool calls accumulate.

    `name="mcp-researcher"` labels this graph — when it's embedded as a
    sub-graph of a future supervisor, the name appears in traces and in
    LangSmith spans, which makes multi-agent runs readable.
    """
    middleware = []
    if max_messages is not None and max_messages > 0:
        middleware.append(_make_trim_middleware(max_messages))

    graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        middleware=middleware,
        name="mcp-researcher",
    )
    log.debug(
        "ReAct graph compiled: llm=%s tools=%d memory=%s trim=%s",
        type(llm).__name__,
        len(tools),
        "on" if checkpointer is not None else "off",
        f"max={max_messages}" if max_messages else "off",
    )
    return graph
