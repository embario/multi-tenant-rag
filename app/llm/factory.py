from __future__ import annotations

import os

from app.llm.app import LLMClient


def get_llm_client() -> LLMClient:
    """Return an LLM client based on environment configuration.

    Environment variables:
    - LLM_PROVIDER: 'openai' (default) or 'stub'
    - LLM_MODEL: model name passed to provider (for openai)
    - DISABLE_EXTERNAL_LLM_CALLS: if '1', prevent external clients from initializing
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    if provider == "openai":
        from app.llm.openai import OpenAIChat

        return OpenAIChat(model=model)

    if provider == "stub":
        from app.llm.stub import StubLLM

        # allow configuring stub behavior via env
        mode = os.getenv("STUB_LLM_MODE", "echo_last_user")
        fixed = os.getenv("STUB_LLM_FIXED", "OK")
        return StubLLM(mode=mode, fixed=fixed)

    raise RuntimeError(f"Unsupported LLM_PROVIDER={provider}")
