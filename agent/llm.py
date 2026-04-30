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

Per-request generation params:
    `ModelParams` carries optional overrides (temperature, top_p,
    max_tokens, plus a free-form `extra` passthrough) supplied by the
    caller of `run_agent()`. Anything missing falls back to the
    deployment default in `agent/config.py`, then to the provider's own
    default. This is the only param-resolution path — once the LLM is
    constructed, the parameters are baked in for the whole turn (LangGraph
    has no per-call kwargs hook for `astream_events`).

    Adding a new portable knob (e.g. `presence_penalty`):
        1. Add the field to `ModelParams` below with a `None` default.
        2. Add a matching `default_<name>` to `AgentConfig` in config.py.
        3. Add a one-liner in `_resolved_kwargs()` to merge it in.
    Provider-specific or rarely-used knobs can skip the first-class
    treatment and ride through `ModelParams.extra`.

Why drop `lru_cache` (compared to the previous implementation):
    Per-request params would either defeat the cache (every request
    constructs anyway) or require freezing params into a hashable key.
    Construction cost is microseconds — provider clients only store
    config; the HTTP transport is lazy — so we just rebuild per call.
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, ConfigDict, Field

from agent.config import settings

log = logging.getLogger(__name__)


class ModelParams(BaseModel):
    """
    Per-request LLM generation parameters. All fields optional.

    Resolution order (first non-None wins):
        per-request value  →  AgentConfig default  →  provider default

    `extra` is a free-form dict spliced into the provider client kwargs
    verbatim. Use it for niche or provider-specific knobs (e.g.
    `presence_penalty` on OpenAI, `top_k` on Anthropic) without bloating
    the schema. Promote a key from `extra` to a first-class field once it
    proves portable across providers.

    `extra="forbid"` makes typos at the API boundary fail loudly rather
    than silently sit in the request body.
    """

    model_config = ConfigDict(extra="forbid")

    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


def _resolved_kwargs(params: ModelParams | None) -> dict[str, Any]:
    """
    Merge per-request params with deployment defaults from `settings`.

    Behaviour:
        - If both per-request and default are None, the key is omitted
          entirely (provider applies its own default).
        - `temperature` is always emitted because the deployment default
          (0.0) is never None — the project intentionally pins it for
          reproducible tool calling unless the caller overrides.
        - `extra` is merged last, so caller-supplied keys win over
          first-class fields if both name the same kwarg (deliberate —
          lets a caller bypass the resolved value when they really need to).
    """
    p = params or ModelParams()
    out: dict[str, Any] = {}

    temp = p.temperature if p.temperature is not None else settings.default_temperature
    if temp is not None:
        out["temperature"] = temp

    top_p = p.top_p if p.top_p is not None else settings.default_top_p
    if top_p is not None:
        out["top_p"] = top_p

    max_tokens = p.max_tokens if p.max_tokens is not None else settings.default_max_tokens
    if max_tokens is not None:
        out["max_tokens"] = max_tokens

    if p.extra:
        out.update(p.extra)

    return out


def get_llm(
    enable_thinking: bool = False,
    params: ModelParams | None = None,
) -> BaseChatModel:
    """
    Construct a chat model for one agent turn.

    Args:
        enable_thinking: Anthropic-only. Switches on extended thinking and
            forces temperature=1 + sufficient max_tokens. Other providers
            silently ignore the flag.
        params: Optional per-request generation parameter overrides. See
            `ModelParams`.

    Returns a fresh `BaseChatModel` — callers should treat it as
    short-lived (one turn). See module docstring for why we don't cache.
    """
    provider = settings.llm_provider.lower()
    kwargs = _resolved_kwargs(params)
    log.info(
        "Initialising LLM: provider=%s model=%s enable_thinking=%s kwargs=%s",
        provider,
        settings.llm_model,
        enable_thinking,
        kwargs,
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
        log.debug("ChatGroq created (enable_thinking ignored for Groq)")
        return ChatGroq(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
            **kwargs,
        )

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY in .env"
            )
        from langchain_anthropic import ChatAnthropic
        if enable_thinking:
            # Anthropic extended thinking constraints (the API rejects
            # anything else):
            #   • temperature must be 1
            #   • max_tokens must exceed budget_tokens
            # Override caller-supplied values that conflict — log a warning
            # so the override is visible rather than silent.
            budget = settings.thinking_budget_tokens
            if kwargs.get("temperature") not in (None, 1, 1.0):
                log.warning(
                    "Anthropic extended thinking forces temperature=1; "
                    "overriding caller value %r",
                    kwargs.get("temperature"),
                )
            kwargs["temperature"] = 1
            min_max_tokens = budget + 4096
            if kwargs.get("max_tokens", 0) < min_max_tokens:
                if "max_tokens" in kwargs:
                    log.warning(
                        "Anthropic extended thinking requires max_tokens > budget; "
                        "raising caller value %r to %d",
                        kwargs["max_tokens"],
                        min_max_tokens,
                    )
                kwargs["max_tokens"] = min_max_tokens
            log.debug("Anthropic extended thinking enabled: budget_tokens=%d", budget)
            return ChatAnthropic(
                model=settings.llm_model,
                api_key=settings.anthropic_api_key,
                thinking={"type": "enabled", "budget_tokens": budget},
                **kwargs,
            )
        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            **kwargs,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        # Ollama uses `num_predict` for the output token cap, not `max_tokens`.
        # Translate so callers can use the portable name everywhere.
        if "max_tokens" in kwargs:
            kwargs["num_predict"] = kwargs.pop("max_tokens")
        # Ollama has no extended-thinking flag; enable_thinking is ignored.
        log.debug("ChatOllama created: base_url=%s (enable_thinking ignored)", settings.ollama_base_url)
        return ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            **kwargs,
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
        # TODO(future): honour enable_thinking for o1/o3 via reasoning_effort,
        # likely sourced from ModelParams.extra to keep the per-provider
        # resolution out of the portable schema.
        base = settings.openai_base_url or "api.openai.com"
        log.debug("ChatOpenAI created: base_url=%s (enable_thinking ignored)", base)
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,  # None → api.openai.com
            **kwargs,
        )

    raise RuntimeError(
        f"Unknown LLM_PROVIDER: {provider!r}. "
        "Supported: groq | anthropic | ollama | openai."
    )
