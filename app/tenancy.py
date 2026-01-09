import uuid
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

tenant_header = APIKeyHeader(
    name="X-Tenant-ID",
    auto_error=False,
)

def get_tenant_id(x_tenant_id: str = Security(tenant_header)) -> uuid.UUID:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header required")
    try:
        return uuid.UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-Tenant-ID")
