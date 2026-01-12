from __future__ import annotations

import os
from typing import Iterable, List

from app.db.models import EMBEDDING_DIM


def batched(items: list[str], batch_size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


class EmbedderProtocol:
    def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError()


class StubEmbedder(EmbedderProtocol):
    """Deterministic local embedder for tests/CI. Returns small deterministic vectors."""
    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        self.dim = dim

    def embed(self, texts: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        for t in texts:
            # Simple deterministic pseudo-embedding: use length and character codes.
            base = float(len(t) % 10)
            vec = [(base + (ord(c) % 7) / 7.0) / (i + 1) for i, c in enumerate((t * ((self.dim // max(1, len(t))) + 1))[: self.dim])]
            # pad/truncate to dim
            if len(vec) < self.dim:
                vec.extend([0.0] * (self.dim - len(vec)))
            else:
                vec = vec[: self.dim]
            out.append(vec)
        return out


def get_embedder():
    """Return an embedder based on environment configuration.

    Env vars:
    - EMBEDDER_PROVIDER: 'openai' (default) or 'stub'
    - DISABLE_EXTERNAL_LLM_CALLS: if '1', prevent external OpenAI embedder from initializing
    """
    provider = os.getenv("EMBEDDER_PROVIDER", "openai").lower()

    if provider == "openai":
        if os.getenv("DISABLE_EXTERNAL_LLM_CALLS") == "1":
            raise RuntimeError("External embedder disabled via DISABLE_EXTERNAL_LLM_CALLS=1")
        from app.ingest.embedder_openai import OpenAIEmbedder

        return OpenAIEmbedder()

    if provider == "stub":
        return StubEmbedder()

    raise RuntimeError(f"Unsupported EMBEDDER_PROVIDER={provider}")
