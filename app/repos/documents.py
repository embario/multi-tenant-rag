import uuid
from sqlalchemy.orm import Session
from app.db.models import Document, DocumentStatus


def get_by_id(db: Session, tenant_id: uuid.UUID, document_id: uuid.UUID):
    """Get a document by its ID within a specific tenant."""
    return (
        db.query(Document)
        .filter(
            Document.tenant_id == tenant_id,
            Document.id == document_id,
        )
        .one_or_none()
    )


def list_for_tenant(db: Session, tenant_id: uuid.UUID):
    """List all documents for a specific tenant."""
    return (
        db.query(Document)
        .filter(Document.tenant_id == tenant_id)
        .order_by(Document.created_at.desc())
        .all()
    )


def create_document(
        db: Session,
        tenant_id: uuid.UUID,
        doc_id: uuid.UUID,
        title: str,
        storage_path: str,
        status: DocumentStatus,
        version: int = 1,
) -> Document:
    """Create a new document for a specific tenant."""
    doc = Document(
        tenant_id=tenant_id,
        id=doc_id,
        title=title,
        source_type="upload",
        storage_path=storage_path,
        status=status,
        version=version,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc