from __future__ import annotations

import uuid
from sqlalchemy.orm import Session
from app.db.models import Chunk


def replace_chunks_for_document(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
    version: int,
    chunk_texts: list[str],
    embeddings: list[list[float]],
) -> int:
    """Replace all chunks for a specific document and version."""
    if len(chunk_texts) != len(embeddings):
        raise ValueError("chunk_texts and embeddings length mismatch")

    # delete existing chunks for this document+version+tenant
    db.query(Chunk).filter(
        Chunk.tenant_id == tenant_id,
        Chunk.document_id == document_id,
        Chunk.version == version,
    ).delete(synchronize_session=False)

    rows: list[Chunk] = []
    for idx, (txt, emb) in enumerate(zip(chunk_texts, embeddings)):
        rows.append(
            Chunk(
                tenant_id=tenant_id,
                document_id=document_id,
                version=version,
                chunk_index=idx,
                text=txt,
                embedding=emb,
                token_count=None,
                meta={},
            )
        )

    db.add_all(rows)
    db.commit()
    return len(rows)
