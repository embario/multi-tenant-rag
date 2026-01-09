from __future__ import annotations

import logging
import time
import uuid
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentStatus
from app.ingest.extract import extract_text
from app.ingest.chunking import chunk_text
from app.ingest.embedder_openai import OpenAIEmbedder, batched
from app.repos import chunks as chunks_repo

log = logging.getLogger("ingest")

def ingest_document(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    document_id: uuid.UUID,
    batch_size: int = 64,
) -> int:
    t0 = time.perf_counter()

    doc = (
        db.query(Document)
        .filter(Document.tenant_id == tenant_id, Document.id == document_id)
        .one_or_none()
    )
    if not doc:
        log.warning("document_not_found tenant_id=%s document_id=%s", tenant_id, document_id)
        raise ValueError("Document not found")

    if not doc.storage_path:
        log.warning("missing_storage_path tenant_id=%s document_id=%s", tenant_id, document_id)
        raise ValueError("Document has no storage_path")

    log.info(
        "ingest_start tenant_id=%s document_id=%s version=%s storage_path=%s status=%s",
        tenant_id, document_id, doc.version, doc.storage_path, doc.status,
    )

    # status transition
    prev = doc.status
    doc.status = DocumentStatus.INGESTING
    db.commit()
    log.info("status_transition tenant_id=%s document_id=%s %s->%s", tenant_id, document_id, prev, doc.status)

    try:
        # Extract
        t_extract = time.perf_counter()
        text = extract_text(doc.storage_path)
        log.info(
            "extract_done tenant_id=%s document_id=%s chars=%s elapsed_ms=%s",
            tenant_id, document_id, len(text), int((time.perf_counter() - t_extract) * 1000),
        )

        # Chunk
        t_chunk = time.perf_counter()
        chunks = chunk_text(text)
        log.info(
            "chunk_done tenant_id=%s document_id=%s chunks=%s elapsed_ms=%s",
            tenant_id, document_id, len(chunks), int((time.perf_counter() - t_chunk) * 1000),
        )

        if not chunks:
            raise ValueError("No text extracted / no chunks produced")

        # Embed (batched)
        embedder = OpenAIEmbedder()
        embeddings: list[list[float]] = []
        total = len(chunks)
        done = 0
        t_embed_all = time.perf_counter()

        for i, batch in enumerate(batched(chunks, batch_size=batch_size), start=1):
            t_batch = time.perf_counter()
            batch_embeddings = embedder.embed(batch)
            embeddings.extend(batch_embeddings)

            done += len(batch)
            log.info(
                "embed_batch_done tenant_id=%s document_id=%s batch=%s batch_size=%s progress=%s/%s elapsed_ms=%s",
                tenant_id, document_id, i, len(batch), done, total, int((time.perf_counter() - t_batch) * 1000),
            )

        log.info(
            "embed_done tenant_id=%s document_id=%s embeddings=%s elapsed_ms=%s",
            tenant_id, document_id, len(embeddings), int((time.perf_counter() - t_embed_all) * 1000),
        )

        # Write chunks
        t_write = time.perf_counter()
        created = chunks_repo.replace_chunks_for_document(
            db,
            tenant_id=tenant_id,
            document_id=document_id,
            version=doc.version,
            chunk_texts=chunks,
            embeddings=embeddings,
        )
        log.info(
            "chunks_written tenant_id=%s document_id=%s created=%s elapsed_ms=%s",
            tenant_id, document_id, created, int((time.perf_counter() - t_write) * 1000),
        )

        doc.status = DocumentStatus.READY
        db.commit()

        log.info(
            "ingest_success tenant_id=%s document_id=%s chunks=%s total_elapsed_ms=%s",
            tenant_id, document_id, created, int((time.perf_counter() - t0) * 1000),
        )
        return created

    except Exception as e:
        doc.status = DocumentStatus.FAILED
        db.commit()
        log.exception(
            "ingest_failed tenant_id=%s document_id=%s total_elapsed_ms=%s err=%r",
            tenant_id, document_id, int((time.perf_counter() - t0) * 1000), e,
        )
        raise
