from __future__ import annotations
import os
from typing import Sequence

from app.llm.app import ChatMessage, LLMClient


class OpenAIChat(LLMClient):
    def __init__(self, model: str) -> None:
        self.model = model

        # Hard guard: never allow this in CI when disabled.
        if os.getenv("DISABLE_EXTERNAL_LLM_CALLS") == "1":
            raise RuntimeError(
                "External LLM calls are disabled (DISABLE_EXTERNAL_LLM_CALLS=1)."
            )

        # Import inside to avoid dependency + accidental init in CI.
        from openai import OpenAI  # type: ignore

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self._client = OpenAI(api_key=api_key)

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        # Keep implementation minimal; adapt to your usage.
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return resp.choices[0].message.content or ""
