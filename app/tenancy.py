import uuid
from fastapi import Header, HTTPException

def get_tenant_id(x_tenant_id: str | None = Header(default=None)) -> uuid.UUID:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")
    try:
        return uuid.UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-Tenant-ID header format")
    
