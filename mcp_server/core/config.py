"""
Server-side config via pydantic-settings.

Why pydantic-settings?
    It reads environment variables (and .env files), validates types, and
    fails *at import time* if anything is broken. That's the whole point —
    a misconfigured server should refuse to start, not explode at the first
    request when the broken var is finally touched.

Validation happens once, here. Everything else in the codebase imports
`settings` and trusts it.
"""
from __future__ import annotations

import json
from functools import cached_property

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # C1: bearer-token → identity map. Static JSON in dev; OAuth 2.1 in prod.
    # TODO(future): replace with OAuth 2.1 issuer config.
    auth_tokens_json: str = (
        '{"tok_alice":{"user_id":"alice","org_id":"acme"}}'
    )

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "documents"

    # Sentence-transformers model name (local, no API key required).
    # Swapping this means rebuilding the Qdrant collection — the vector
    # dimension is baked into the collection at creation time.
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── Parsed view of auth_tokens_json ──────────────────────────────────
    @cached_property
    def auth_tokens(self) -> dict[str, dict[str, str]]:
        # Cheap because the validator below guarantees the raw string parses.
        return json.loads(self.auth_tokens_json)

    # ── Startup-time validation: bad JSON should kill the process here ───
    @field_validator("auth_tokens_json")
    @classmethod
    def _validate_tokens_json(cls, v: str) -> str:
        try:
            parsed = json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"AUTH_TOKENS_JSON is not valid JSON: {e}") from e
        if not isinstance(parsed, dict):
            raise ValueError("AUTH_TOKENS_JSON must be a JSON object")
        for tok, ident in parsed.items():
            if (
                not isinstance(ident, dict)
                or "user_id" not in ident
                or "org_id" not in ident
            ):
                raise ValueError(
                    f"AUTH_TOKENS_JSON[{tok!r}] must be an object with "
                    "'user_id' and 'org_id' keys"
                )
        return v


settings = ServerConfig()
