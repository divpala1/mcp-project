"""
LLM factory — the single point in the codebase where a specific provider
is imported.

C4 — provider swap:
    Change `LLM_PROVIDER` + `LLM_MODEL` in .env. Nothing else changes.
    The rest of the codebase only ever sees a `BaseChatModel`.

Why lazy imports inside each branch?
    Each provider package pulls its own transport deps. If a user only
    wants Groq, they shouldn't pay the import cost for Anthropic + Ollama.
    Moving `from langchain_groq import ChatGroq` into the `groq` branch
    keeps cold-start clean.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from agent.config import settings

log = logging.getLogger(__name__)


# Memoized by (provider, model, enable_thinking) — at most 2 live instances
# (thinking on/off). Bools are hashable so lru_cache works fine.
@lru_cache(maxsize=2)
def get_llm(enable_thinking: bool = False) -> BaseChatModel:
    provider = settings.llm_provider.lower()
    log.info(
        "Initialising LLM: provider=%s model=%s enable_thinking=%s",
        provider,
        settings.llm_model,
        enable_thinking,
    )

    if provider == "groq":
        if not settings.groq_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=groq requires GROQ_API_KEY in .env"
            )
        from langchain_groq import ChatGroq
        # Groq has no extended-thinking parameter; enable_thinking is silently
        # ignored. Groq reasoning models (deepseek-r1, qwq) think internally
        # and don't need a separate flag.
        llm = ChatGroq(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
            # temperature=0 for reproducible tool-calling behaviour while
            # learning. Raise it when you want more creative prose.
            temperature=0,
        )
        log.debug("ChatGroq created (enable_thinking ignored for Groq)")
        return llm

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY in .env"
            )
        from langchain_anthropic import ChatAnthropic
        if enable_thinking:
            # Anthropic extended thinking constraints:
            #   • temperature must be 1 (API rejects other values)
            #   • max_tokens must exceed budget_tokens (we add headroom)
            budget = settings.thinking_budget_tokens
            log.debug("Anthropic extended thinking enabled: budget_tokens=%d", budget)
            return ChatAnthropic(
                model=settings.llm_model,
                api_key=settings.anthropic_api_key,
                temperature=1,
                max_tokens=budget + 4096,
                thinking={"type": "enabled", "budget_tokens": budget},
            )
        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            temperature=0,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        # Ollama has no extended-thinking flag; enable_thinking is ignored.
        log.debug("ChatOllama created: base_url=%s (enable_thinking ignored)", settings.ollama_base_url)
        return ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )

    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=openai requires OPENAI_API_KEY in .env"
            )
        from langchain_openai import ChatOpenAI
        # `base_url` is the universal knob. Leave it unset for the real OpenAI
        # API; point it at any OpenAI-compatible endpoint to use a different
        # provider (Together AI, Fireworks, LM Studio, Cerebras, …) — no code
        # changes needed, just env vars.
        #
        # enable_thinking: OpenAI reasoning models (o1, o3) use a different
        # mechanism (`reasoning_effort`, not a thinking block). We ignore the
        # flag here for simplicity.
        # TODO(future): honour enable_thinking for o1/o3 via reasoning_effort.
        base = settings.openai_base_url or "api.openai.com"
        log.debug("ChatOpenAI created: base_url=%s (enable_thinking ignored)", base)
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,  # None → api.openai.com
            temperature=0,
        )

    raise RuntimeError(
        f"Unknown LLM_PROVIDER: {provider!r}. "
        "Supported: groq | anthropic | ollama | openai."
    )
