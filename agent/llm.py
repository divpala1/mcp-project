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

from langchain_core.language_models import BaseChatModel

from agent.config import settings


def get_llm() -> BaseChatModel:
    provider = settings.llm_provider.lower()

    if provider == "groq":
        if not settings.groq_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=groq requires GROQ_API_KEY in .env"
            )
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
            # temperature=0 for reproducible tool-calling behaviour while
            # learning. Raise it when you want more creative prose.
            temperature=0,
        )

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY in .env"
            )
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            temperature=0,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )

    raise RuntimeError(
        f"Unknown LLM_PROVIDER: {provider!r}. "
        "Supported: groq | anthropic | ollama."
    )
