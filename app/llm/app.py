from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMClient(Protocol):
    def chat(self, messages: Sequence[ChatMessage]) -> str:
        ...
