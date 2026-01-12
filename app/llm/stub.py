from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

from app.llm.app import ChatMessage, LLMClient


@dataclass
class StubLLM(LLMClient):
    """
    Deterministic, local-only LLM for tests and CI.
    You can make it smarter over time (rule-based responses).
    """
    mode: str = "echo_last_user"  # or "fixed"
    fixed: str = "OK"

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        if self.mode == "fixed":
            return self.fixed

        # Echo last user message (useful for testing plumbing)
        for m in reversed(messages):
            if m.role == "user":
                return m.content
        return ""
