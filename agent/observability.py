"""
Optional LangSmith tracing.

Design stance: observability is *opt-in*, not a hard dependency. If
`LANGSMITH_API_KEY` is unset, this module is a no-op — the agent runs
fine without it. Flip the key on and every LLM call + tool call shows
up as a span in the LangSmith UI, which is invaluable for:
  - Debugging "the LLM keeps calling the wrong tool" — you can see the
    tool schema it was given.
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

from agent.config import settings

log = logging.getLogger(__name__)


def setup_tracing() -> None:
    """
    LangSmith tracing is driven by env vars read by langchain-core at
    import time (via the LangSmith client). Setting them here is
    effectively a last-chance override — fine because we call this
    before any LangChain object is constructed.
    """
    if not settings.langsmith_api_key:
        log.info("LANGSMITH_API_KEY not set — tracing disabled.")
        return
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    log.info("LangSmith tracing enabled: project=%s", settings.langsmith_project)
