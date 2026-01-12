import uuid
from app.db.models import Chunk, Document, DocumentStatus


def test_missing_tenant_header(client):
    r = client.get("/documents/some-uuid")
    assert r.status_code == 400


def test_document_isolation(client, tenant_ids):
    tenant_a = tenant_ids["tenant_a"]
    tenant_b = tenant_ids["tenant_b"]

    # create doc in tenant A
    r = client.post(
        "/documents",
        headers={"X-Tenant-ID": str(tenant_a)},
        files={"file": ("test.txt", b"hello", "text/plain")},
        data={"title": "test"},
    )
    assert r.status_code == 200
    doc_id = r.json()["id"]

    # attempt read as tenant B
    r2 = client.get(f"/documents/{doc_id}", headers={"X-Tenant-ID": str(tenant_b)})
    assert r2.status_code == 404


def test_ingest_creates_chunks_with_stub_embedder(
    client, db_session, monkeypatch, tmp_path, tenant_ids
):
    tenant_id = tenant_ids["tenant_a"]

    # Ensure environment uses stub embedder and local uploads path for CI/testing.
    monkeypatch.setenv("EMBEDDER_PROVIDER", "stub")
    monkeypatch.setenv("DISABLE_EXTERNAL_LLM_CALLS", "1")
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))

    # Upload a document (simple text payload).
    create_resp = client.post(
        "/documents",
        headers={"X-Tenant-ID": str(tenant_id)},
        files={"file": ("stub.txt", b"hello from stub", "text/plain")},
        data={"title": "stub doc"},
    )
    assert create_resp.status_code == 200
    doc_id = create_resp.json()["id"]

    # Trigger ingest – should use StubEmbedder to generate embeddings deterministically.
    ingest_resp = client.post(
        f"/documents/{doc_id}/ingest",
        headers={"X-Tenant-ID": str(tenant_id)},
    )
    assert ingest_resp.status_code == 200
    assert ingest_resp.json()["chunks_created"] > 0

    # Verify chunks were persisted for this document.
    chunks = db_session.query(Chunk).filter(Chunk.document_id == doc_id).all()
    assert chunks, "Expected chunks to exist after ingest with stub embedder"


def test_get_document_success(client, monkeypatch, tmp_path, tenant_ids):
    tenant_id = tenant_ids["tenant_a"]
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))

    create_resp = client.post(
        "/documents",
        headers={"X-Tenant-ID": str(tenant_id)},
        files={"file": ("readme.txt", b"content", "text/plain")},
        data={"title": "readme"},
    )
    assert create_resp.status_code == 200
    doc_id = create_resp.json()["id"]

    get_resp = client.get(
        f"/documents/{doc_id}",
        headers={"X-Tenant-ID": str(tenant_id)},
    )
    assert get_resp.status_code == 200
    payload = get_resp.json()
    assert payload["id"] == doc_id
    assert payload["title"] == "readme"
    assert payload["storage_path"].startswith(str(tmp_path))


def test_create_document_missing_tenant_returns_404(client, tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    orphan_tenant = uuid.uuid4()
    resp = client.post(
        "/documents",
        headers={"X-Tenant-ID": str(orphan_tenant)},
        files={"file": ("test.txt", b"hi", "text/plain")},
        data={"title": "orphan"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Tenant not found"


def test_create_document_empty_file_rejected(client, tmp_path, monkeypatch, tenant_ids):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    tenant_id = tenant_ids["tenant_a"]

    resp = client.post(
        "/documents",
        headers={"X-Tenant-ID": str(tenant_id)},
        files={"file": ("empty.txt", b"", "text/plain")},
        data={"title": "empty"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Uploaded file is empty"


def test_ingest_missing_document_returns_404(client, tenant_ids):
    tenant_id = tenant_ids["tenant_a"]

    missing_doc = uuid.uuid4()
    resp = client.post(
        f"/documents/{missing_doc}/ingest",
        headers={"X-Tenant-ID": str(tenant_id)},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Document not found"


def test_get_document_missing_returns_404(client, tenant_ids):
    resp = client.get(
        f"/documents/{uuid.uuid4()}",
        headers={"X-Tenant-ID": str(tenant_ids["tenant_a"])},
    )
    assert resp.status_code == 404


def test_create_document_sanitizes_filename_and_writes_file(
    client, monkeypatch, tmp_path, tenant_ids
):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    resp = client.post(
        "/documents",
        headers={"X-Tenant-ID": str(tenant_ids["tenant_a"])},
        files={"file": ("../weird/../../secret.pdf", b"content", "application/pdf")},
        data={"title": "sanity"},
    )
    assert resp.status_code == 200
    payload = resp.json()
    storage_path = payload["storage_path"]
    assert storage_path.startswith(str(tmp_path))
    stored_file = tmp_path / storage_path.split("/")[-1]
    assert stored_file.exists()


def test_ingest_document_without_storage_path_returns_404(
    client, db_session, tenant_ids
):
    tenant_id = tenant_ids["tenant_a"]
    doc = Document(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        title="broken",
        source_type="upload",
        storage_path=None,
        status=DocumentStatus.CREATED,
        version=1,
    )
    db_session.add(doc)
    db_session.commit()

    resp = client.post(
        f"/documents/{doc.id}/ingest",
        headers={"X-Tenant-ID": str(tenant_id)},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Document has no storage_path"
