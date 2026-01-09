from uuid import UUID
from app.db.session import SessionLocal
from app.db.models import Tenant

TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

db = SessionLocal()

if not db.query(Tenant).filter_by(id=TENANT_ID).first():
    db.add(Tenant(id=TENANT_ID, name="sample-tenant"))
    db.commit()
