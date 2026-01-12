from __future__ import annotations
from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class DocumentCreateResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    title: str
    source_type: str = "upload"
    status: str
    version: int
    storage_path: Optional[str] = None
