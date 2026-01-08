import uuid
from app.db.models import Tenant

TENANT_A = uuid.UUID("00000000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("00000000-0000-0000-0000-000000000002")


def test_missing_tenant_header(client):
    r = client.get("/documents/some-uuid")
    assert r.status_code == 400


def test_document_isolation(client, db_session):
    # ensure both tenants exist
    db_session.merge(Tenant(id=TENANT_A, name="tenant-a"))
    db_session.merge(Tenant(id=TENANT_B, name="tenant-b"))
    db_session.commit()

    # create doc in tenant A
    r = client.post(
        "/documents",
        headers={"X-Tenant-ID": str(TENANT_A)},
        files={"file": ("test.txt", b"hello", "text/plain")},
        data={"title": "test"},
    )
    assert r.status_code == 200
    doc_id = r.json()["id"]

    # attempt read as tenant B
    r2 = client.get(f"/documents/{doc_id}", headers={"X-Tenant-ID": str(TENANT_B)})
    assert r2.status_code == 404


