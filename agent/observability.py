"""
Optional observability backends: LangSmith and Langfuse.

Design stance: both are *opt-in*, not hard dependencies. The agent runs
fine with neither key set. Enable one or both — they work simultaneously
because they use independent mechanisms:
  - LangSmith captures spans automatically via env vars read by langchain-core.
  - Langfuse captures spans via a CallbackHandler injected into run_config.

Either backend is invaluable for:
  - Debugging "the LLM keeps calling the wrong tool" — you see the exact
    tool schema it received.
  - Catching ReAct loop stalls (infinite tool calls, unexpected halt).
  - Comparing runs when you swap LLM_PROVIDER — side-by-side traces.

# NOTE(observability): this is where an evaluation harness would plug in.
# Use LangSmith datasets + evaluators to regression-test prompt/tool changes.
# TODO(future): add eval harness (probably pytest + LangSmith's
# `langsmith.evaluation.evaluate` when the agent matures).
"""
from __future__ import annotations

import logging
import os
from contextvars import ContextVar
from typing import Any

from agent.config import settings

log = logging.getLogger(__name__)

# ─── Per-request token tag ─────────────────────────────────────────────────────
# Stored in a ContextVar so each asyncio Task (= each concurrent request)
# carries its own value. Call set_request_token() once at the request
# boundary; every log line in that task's call stack gets the tag for free
# via _TokenTagFormatter, without any manual passing.
#
# Default "-" appears on startup/teardown logs that belong to no request.
_request_token: ContextVar[str] = ContextVar("_request_token", default="-")

# Log format shared between CLI (main.py basicConfig) and non-CLI (uvicorn).
# %(token_tag)s is injected by _TokenTagFormatter below.
_LOG_FORMAT = "%(asctime)s %(levelname)s [%(token_tag)s] %(name)s — %(message)s"


class _TokenTagFormatter(logging.Formatter):
    """
    Formatter that injects `token_tag` from the current async context.

    Why a Formatter and not a Filter?
        logging.Filter added to the ROOT LOGGER is only consulted when a
        record is logged via the root logger itself. Records from child
        loggers (agent.core, agent.tools, …) propagate to the root's
        *handlers* via Logger.callHandlers(), which calls handler.handle()
        directly — bypassing Logger.handle() and therefore the root logger's
        own filter() method entirely. Adding the filter to the root logger
        simply does not work for child-logger records.

        A Formatter runs inside handler.emit(), which IS called for every
        record that reaches the handler regardless of which child logger
        produced it. Reading the ContextVar here is the correct place.
    """

    def format(self, record: logging.LogRecord) -> str:
        record.token_tag = _request_token.get()  # type: ignore[attr-defined]
        return super().format(record)


def set_request_token(token: str) -> None:
    """
    Stamp all log lines in the current async context with a token prefix.

    Call once at the entry point of every request (run_agent in core.py
    for the CLI path; the API endpoint in api.py for the HTTP path). Every
    log.* call anywhere in the call stack — llm.py, tools.py, toolset.py,
    etc. — automatically includes the tag without any manual threading.

    Only the first 8 characters of the token are used (e.g. "tok_alic…"),
    enough to identify the caller without exposing the credential.
    """
    tag = (token[:8] + "…") if token else "<empty>"
    _request_token.set(tag)


def configure_logging() -> None:
    """
    Idempotent logging bootstrap: installs _TokenTagFormatter on the root
    logger's handlers so every log line carries the current request's token.

    Called from:
      - main.py at process start (before anything else logs).
      - setup_tracing() for non-CLI entry points (uvicorn may have already
        installed its own handlers; we update their formatters in place).

    Why update handler formatters directly?
        logging.basicConfig() is a no-op when handlers already exist
        (e.g. after uvicorn installs its StreamHandler). We must set the
        formatter on existing handlers explicitly.
    """
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)
    logging.root.setLevel(logging.INFO)

    # Apply _TokenTagFormatter to every handler currently on the root logger.
    # This covers both the handler basicConfig just created (if any) and
    # handlers uvicorn installed before our code ran.
    formatter = _TokenTagFormatter(_LOG_FORMAT)
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)


def setup_tracing() -> None:
    """
    LangSmith tracing is driven by env vars read by langchain-core at
    import time (via the LangSmith client). Setting them here is
    effectively a last-chance override — fine because we call this
    before any LangChain object is constructed.

    Also ensures the root logger is configured when called from a non-CLI
    entry point (e.g. uvicorn). configure_logging() is idempotent so
    calling it here is safe even if main.py already ran it.
    """
    configure_logging()
    # Quiet noisy third-party loggers regardless of entry point.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("mcp").setLevel(logging.WARNING)

    if not settings.langsmith_api_key:
        log.info("LANGSMITH_API_KEY not set — LangSmith tracing disabled.")
        return
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    log.info("LangSmith tracing enabled: project=%s", settings.langsmith_project)


def build_langfuse_callback() -> Any | None:
    """
    Return a Langfuse CallbackHandler for LangChain/LangGraph, or None if
    Langfuse credentials are not configured.

    Why a callback (not env vars like LangSmith)?
        Langfuse's LangChain integration uses a per-run callback object rather
        than global env vars. This means it captures spans from the exact
        graph invocation it is passed to, with no cross-contamination between
        concurrent requests — a cleaner model for async servers.

    The returned handler is passed into run_config["callbacks"] in core.py.
    LangGraph propagates it to every node automatically, so LLM calls, tool
    calls, and the ReAct loop all appear as child spans under the same trace.

    Lazy import: `langfuse` is an optional dependency. Importing at module
    level would crash the agent on startup if the package is not installed.
    We only reach this code path when both keys are set, so the user has
    opted in and the package should be present.
    """
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        log.info("LANGFUSE_PUBLIC_KEY / SECRET_KEY not set — Langfuse tracing disabled.")
        return None

    try:
        from langfuse import Langfuse  # type: ignore[import]
        from langfuse.langchain import CallbackHandler  # type: ignore[import]
    except ImportError:
        log.warning(
            "langfuse package not installed — Langfuse tracing disabled. "
            "Run: pip install 'langfuse>=2.0.0'"
        )
        return None

    # Langfuse v3: credentials inputted in the Langfuse client
    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    log.info("Langfuse tracing enabled: host=%s", settings.langfuse_host)
    return CallbackHandler()
