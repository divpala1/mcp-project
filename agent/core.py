"""
Framework-free agent entry point.

This is the seam every host uses — CLI, FastAPI, tests. It knows nothing
about HTTP, SSE response framing, request schemas, or argv. It accepts
plain Python inputs (prompt + auth token + optional MCP server override),
runs one turn of the agent, and yields structured `AgentEvent` dicts.

Each caller decides how to render the events:
    - CLI (agent/main.py)   → print() with emoji markers, current behavior.
    - FastAPI (agent/api.py) → format as SSE `data:` frames, stream to client.
    - Tests / scripts        → assert on event sequence and content.

Why an async generator (not a list, not a callback):
    LangGraph's `astream_events` is itself an async iterator that emits
    incrementally. Buffering it into a list would defeat the whole point
    (token-by-token UX). A callback-based API would force every host into
    the same control-flow shape. An async generator is the universal
    consumer-friendly form — you can `async for ev in run_agent(...)` from
    any async context.

# NOTE(memory): when long-term / per-conversation memory lands, this is
# the function that grows extra inputs (`session_id`, `user_id`) and the
# message history will be loaded from a checkpointer instead of starting
# from a single HumanMessage. CLAUDE.md item #11.
"""
from __future__ import annotations

import logging
import time
from typing import Any, AsyncIterator, Literal, TypedDict

from agent.agent import build_agent
from agent.config import McpServerSpec, default_mcp_servers, settings
from agent.llm import get_llm
from agent.observability import build_langfuse_callback, set_request_token, setup_tracing
from agent.prompts import get_prompt, get_prompt_version
from agent.tools import compile_tools

log = logging.getLogger(__name__)


class AgentEvent(TypedDict, total=False):
    """
    Discriminated event union, encoded as a TypedDict for simplicity.

    `type` field decides which other fields are present:
        token        text: str
        tool_start   name: str, args: Any
        tool_end     name: str, output: Any
        error        message: str
        end          (no extra fields — terminator marker)

    Kept deliberately tiny. Fields can be added without breaking existing
    consumers since they read by key.
    """
    type: Literal["token", "tool_start", "tool_end", "error", "end"]
    text: str
    name: str
    args: Any
    output: Any
    message: str


async def run_agent(
    prompt: str,
    *,
    auth_token: str,
    mcp_servers: dict[str, McpServerSpec] | None = None,
    enable_thinking: bool = False,
    user_id: str | None = None,
    session_id: str | None = None,
) -> AsyncIterator[AgentEvent]:
    """
    Run the agent for one turn and yield structured events.

    Args:
        prompt: The user's message for this turn.
        auth_token: Bearer token forwarded to MCP servers. The MCP server
            validates and resolves to {user_id, org_id}; Qdrant filters
            scope to that org. The agent never inspects the token itself
            — it's an opaque pass-through.
        mcp_servers: Optional override of the server dict. If None, falls
            back to env-driven defaults via `default_mcp_servers()`.
            Production hosts that resolve servers per user/org pass a
            fully-formed dict here.
        enable_thinking: When True, enables extended thinking for Anthropic
            models (temperature=1, thinking budget applied). Has no effect
            on Groq or Ollama providers — those are silently ignored.
        user_id: Human-readable user identifier forwarded to Langfuse as
            the trace's first-class `user_id`. Enables "filter by user" in
            the Langfuse UI. If None, falls back to `auth_token` so every
            trace is still attributable — just by token rather than name.
            Production API gateways that resolve the token to a real
            identity (e.g. "alice@acme.com") should pass it here.
        session_id: Optional conversation/session identifier. Langfuse
            groups all traces with the same session_id under one session
            view. Useful for multi-turn conversation threads once memory
            lands. Leave None for single-turn CLI usage.

    Yields:
        AgentEvent dicts in the order they occur. Always terminated by an
        `end` event, even on error (an `error` event is emitted first).
    """
    setup_tracing()
    # Stamp every log line in this async context with the caller's token tag.
    # All downstream calls (llm.py, tools.py, toolset.py, …) inherit this
    # automatically via the _TokenTagFilter on the root logger.
    set_request_token(auth_token)

    log.info(
        "run_agent started: prompt_len=%d enable_thinking=%s servers=%s",
        len(prompt),
        enable_thinking,
        "override" if mcp_servers is not None else "env-default",
    )
    t0 = time.monotonic()

    try:
        llm = get_llm(enable_thinking=enable_thinking)
        servers = mcp_servers if mcp_servers is not None else default_mcp_servers()

        # Tool composition is delegated to agent/toolset.py. That module
        # merges MCP-loaded tools with locally-registered tools (see
        # agent/registry.py) and is the future seam for a tool-finder
        # layer (CLAUDE.md C2a). It never raises — failures are mapped to
        # `notools_reason`, a short string the no-tool system prompt
        # surfaces to the LLM so the model can explain the situation.
        tools, notools_reason = await compile_tools(
            mcp_servers=servers,
            auth_token=auth_token,
        )

        # Select the system prompt based on whether any tools loaded.
        # When tools are available, the catalog is rendered into the template
        # so the LLM sees exactly what it can call — adding a server-side
        # @mcp.tool() automatically surfaces here with no agent-side edit.
        # When no tools loaded, a minimal no-tool prompt is used — the full
        # tool-guidance sections would only pollute the context window.
        if tools:
            prompt_name = "system"
            system_prompt = get_prompt("system")
        else:
            prompt_name = "system_notools"
            system_prompt = get_prompt("system_notools", reason=notools_reason)

        agent = build_agent(llm, tools, system_prompt=system_prompt)
        log.info("Agent compiled with %d tools, prompt=%s", len(tools), prompt_name)

        # Tag every span in this run with the prompt version. LangSmith
        # records this as run metadata; you can group/filter runs by it
        # to compare behaviour across prompt revisions (e.g. system@v1
        # vs system@v2). The version comes from the frontmatter in the
        # prompt's .md file.
        #
        # Callbacks: Langfuse uses a per-run CallbackHandler (unlike LangSmith
        # which reads global env vars). Passing it here causes LangGraph to
        # propagate it to every node automatically — LLM calls and tool calls
        # all become child spans under the same trace, with no extra wiring.
        #
        # Langfuse v3 metadata keys (set here, not on the CallbackHandler
        # constructor — v3 CallbackHandler takes no parameters):
        #
        #   langfuse_user_id  → Langfuse's first-class "User" field.
        #                       Enables "filter by user" in the UI and the
        #                       per-user usage/cost dashboard. Falls back to
        #                       auth_token when no resolved identity is known
        #                       (consistent with the token tag on log lines).
        #
        #   langfuse_session_id → Groups traces under one session view.
        #                         Useful once multi-turn memory lands.
        #
        #   langfuse_tags     → Free-form string tags for slice-and-dice.
        #                       We include provider + model so you can filter
        #                       all traces for a given model in one click,
        #                       without needing to open individual spans.
        #                       Model is also auto-captured inside generation
        #                       spans, but trace-level tags surface it in the
        #                       trace list view where per-span detail isn't shown.
        callbacks = []
        lf_callback = build_langfuse_callback()
        if lf_callback:
            callbacks.append(lf_callback)
            log.debug("Langfuse callback attached to run_config")

        prompt_version = f"{prompt_name}@{get_prompt_version(prompt_name)}"
        langfuse_tags = [
            f"provider:{settings.llm_provider}",
            f"model:{settings.llm_model}",
        ]
        metadata: dict[str, Any] = {
            "prompt_version": prompt_version,
            "langfuse_user_id": user_id or auth_token,
            "langfuse_tags": langfuse_tags,
        }
        if session_id:
            metadata["langfuse_session_id"] = session_id

        run_config = {
            "metadata": metadata,
            "callbacks": callbacks,
        }
        log.debug(
            "run_config: prompt_version=%s callbacks=%d",
            prompt_version,
            len(callbacks),
        )

        # Track whether the previous emission was a streaming text chunk;
        # callers that render to a terminal use this to break lines around
        # tool boundaries. FastAPI/SSE consumers don't care — they just
        # forward each event verbatim.
        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": prompt}]},
            version="v2",
            config=run_config,
        ):
            kind = event.get("event")
            if kind is None:
                log.debug("Skipping event with no 'event' key: %r", event)
                continue

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                # chunk.content is str on most providers; Anthropic-style
                # providers return a list of content blocks. Normalize both.
                content = chunk.content
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    parts = []
                    for block in content:
                        if isinstance(block, dict) and "text" in block:
                            parts.append(block["text"])
                        elif not isinstance(block, dict):
                            log.debug("Skipped non-dict content block: %r", block)
                    text = "".join(parts)
                else:
                    log.warning("Unexpected chunk.content type %s; skipping", type(content).__name__)
                    text = ""
                if text:
                    yield {"type": "token", "text": text}
            elif kind == "on_tool_start":
                tool_name = event.get("name", "<tool>")
                tool_args = event["data"].get("input", {})
                log.debug("tool_start: %s args=%r", tool_name, tool_args)
                yield {
                    "type": "tool_start",
                    "name": tool_name,
                    "args": tool_args,
                }
            elif kind == "on_tool_end":
                tool_name = event.get("name", "<tool>")
                tool_output = event["data"].get("output")
                log.debug("tool_end: %s output=%r", tool_name, tool_output)
                yield {
                    "type": "tool_end",
                    "name": tool_name,
                    "output": tool_output,
                }
    except Exception as exc:
        # Surface errors as a structured event rather than letting the
        # generator raise. The three failures most worth surfacing here:
        #   - MCP handshake / auth rejection (bad bearer token → 401)
        #   - LLM provider error (rate limit, bad credentials)
        #   - LLM tool-call validation (Groq's "Failed to call a function"
        #     response — the offending generation lives in exc.body and is
        #     the only useful thing to read; without it the message is
        #     opaque). We pull it out for both the log and the SSE event.
        body = getattr(exc, "body", None)
        failed_generation = None
        if isinstance(body, dict):
            failed_generation = body.get("failed_generation")
        if failed_generation:
            log.exception(
                "Agent run failed — provider rejected generation:\n%s",
                failed_generation,
            )
            yield {
                "type": "error",
                "message": (
                    f"{type(exc).__name__}: {exc}\n"
                    f"failed_generation: {failed_generation}"
                ),
            }
        else:
            log.exception("Agent run failed")
            yield {"type": "error", "message": f"{type(exc).__name__}: {exc}"}
    finally:
        elapsed = time.monotonic() - t0
        log.info("run_agent finished in %.2fs", elapsed)
        yield {"type": "end"}
