from __future__ import annotations

def chunk_text(text: str, *, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    # normalize whitespace
    text = " ".join(text.split())
    if not text:
        return []

    chunks: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        end = min(n, i + chunk_size)
        chunks.append(text[i:end])
        if end == n:
            break
        i = max(0, end - overlap)

    return chunks
