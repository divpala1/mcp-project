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
from typing import Any

from agent.config import settings

log = logging.getLogger(__name__)


def setup_tracing() -> None:
    """
    LangSmith tracing is driven by env vars read by langchain-core at
    import time (via the LangSmith client). Setting them here is
    effectively a last-chance override — fine because we call this
    before any LangChain object is constructed.

    Also ensures the root logger is configured at INFO when this is
    called from a non-CLI entry point (e.g. uvicorn). `basicConfig` is a
    no-op if handlers already exist, so it won't override uvicorn's own
    logging setup — but it *will* set the level on uvicorn's existing
    root handler if one was installed. We call `logging.root.setLevel`
    explicitly to cover that case.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    logging.root.setLevel(logging.INFO)
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
