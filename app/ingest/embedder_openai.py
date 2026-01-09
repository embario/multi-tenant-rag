from __future__ import annotations

import os
from typing import Iterable

from openai import OpenAI

EMBED_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

class OpenAIEmbedder:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.client = OpenAI(api_key=api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        # OpenAI embeddings: pass list of strings, request float output explicitly
        resp = self.client.embeddings.create(
            model=EMBED_MODEL,
            input=texts,
            encoding_format="float",
        )
        # preserve input order
        data = sorted(resp.data, key=lambda d: d.index)
        return [d.embedding for d in data]


def batched(items: list[str], batch_size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]
