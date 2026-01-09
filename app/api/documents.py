from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from uuid import UUID
from app.tenancy import get_tenant_id
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import DocumentCreateResponse
from app.db.deps import get_db
from app.db.models import Document, DocumentStatus, Tenant
from app.repos import documents as document_repo
from app.ingest.service import ingest_document

log = logging.getLogger("api.documents")

router = APIRouter(prefix='/documents', tags=['documents'])

def _safe_filename(original: str) -> str:
    # keep it simple; prevent path traversal
    name = Path(original).name
    return name.replace("\x00", "")  # remove null bytes


@router.get("/{doc_id}")
def get_document(
    doc_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    doc = document_repo.get_by_id(db, tenant_id, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("", response_model=DocumentCreateResponse)
def create_document(
    tenant_id: UUID = Depends(get_tenant_id),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentCreateResponse:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    upload_dir = os.environ.get("UPLOAD_DIR", "/app/uploads")
    Path(upload_dir).mkdir(parents=True, exist_ok=True)

    doc_id = uuid.uuid4()
    safe_name = _safe_filename(file.filename or "upload.bin")
    ext = Path(safe_name).suffix.lower()[:20]  # limit extension length
    stored_name = f"{doc_id}{ext}"
    storage_path = str(Path(upload_dir) / stored_name)

    # save file to disk
    with open(storage_path, "wb") as out_file:
        content = file.file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        out_file.write(content)

    doc = document_repo.create_document(
        db,
        tenant.id,
        doc_id=doc_id,
        title=title,
        storage_path=storage_path,
        status=DocumentStatus.CREATED,
        version=1,
    )

    return DocumentCreateResponse(
        id=doc.id,
        tenant_id=doc.tenant_id,
        title=doc.title,
        source_type=doc.source_type,
        status=doc.status,
        version=doc.version,
        storage_path=doc.storage_path,
)

@router.post("/{doc_id}/ingest")
def ingest_doc(
    doc_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    log.info("ingest_endpoint_called tenant_id=%s document_id=%s", tenant_id, doc_id)
    try:
        n = ingest_document(db, tenant_id=tenant_id, document_id=doc_id)
        log.info("ingest_endpoint_ok tenant_id=%s document_id=%s chunks_created=%s", tenant_id, doc_id, n)
        return {"document_id": str(doc_id), "chunks_created": n}
    except ValueError as e:
        log.warning("ingest_endpoint_value_error tenant_id=%s document_id=%s err=%s", tenant_id, doc_id, str(e))
        raise HTTPException(status_code=404, detail=str(e))

