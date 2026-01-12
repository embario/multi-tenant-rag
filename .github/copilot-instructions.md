# Copilot Instructions for Multi-Tenant RAG

Short, actionable guidance to help AI coding agents be productive working on this repository.

Architecture Summary
- The service is a Python FastAPI backend providing a multi-tenant Retrieval-Augmented Generation (RAG) API.
- Major components:
  - API: `app/main.py` and `app/api/*` (e.g., `app/api/documents.py`) implement HTTP endpoints.
  - Tenancy: `app/tenancy.py` enforces tenant isolation via `X-Tenant-ID` header.
  - Database models: `app/db/models.py` contains SQLAlchemy models (Tenant, User, Document, Chunk, ACLs, QueryLog, EvalRun).
  - DB wiring: `app/db/session.py` + `app/db/deps.py` provide `SessionLocal` and `get_db` dependency.
  - Ingest pipeline: `app/ingest/*` contains extraction, chunking, embedding, and `app/ingest/service.py` orchestrates ingestion.
  - Repositories: `app/repos/*` (e.g., `documents.py`, `chunks.py`) encapsulate DB operations.
  - Embeddings: `app/ingest/embedder_openai.py` wraps OpenAI embeddings client.
  - Embeddings: `app/ingest/embedder_openai.py` wraps OpenAI embeddings client.
  - Chat / LLM clients: `app/llm/` contains providers and a factory (`get_llm_client`) to select an LLM implementation based on environment variables.

Key Design Decisions & Why
- Tenant isolation is enforced at the API and DB layer: requests must include `X-Tenant-ID` (see `get_tenant_id`), and repo queries always filter by `tenant_id`.
- Chunks are versioned per document (`version` column) allowing re-ingest without clobbering historical versions.
- Embeddings are stored as PGVector columns (`pgvector`) and indexing is expected to be added via migrations (see `alembic/versions`).
- The ingest pipeline is synchronous in `ingest_document` (single-threaded commit semantics). Keep changes minimal and follow repo patterns when adding async/parallel work.

Developer Workflows (commands & environment)
- Quick local run (docker): follow README.md — copy `.env.example` to `.env` and run:

```bash
docker compose up --build
```

- Important env vars:
  - `DATABASE_URL` (Postgres DSN, used by SQLAlchemy)
  - `UPLOAD_DIR` (default `/app/uploads`) used by `app/api/documents.py` for file storage
  - `OPENAI_API_KEY` and optionally `OPENAI_EMBEDDING_MODEL` for embeddings
  - `LLM_PROVIDER` (optional) — choose LLM provider: `openai` (default) or `stub`
  - `LLM_MODEL` (optional) — model name passed to the chosen provider (e.g., `gpt-4o-mini`)
  - `DISABLE_EXTERNAL_LLM_CALLS` (optional) — set to `1` to prevent external LLM initialization (CI safety)
  - `EMBEDDER_PROVIDER` (optional) — choose embedder: `openai` (default) or `stub` for CI

- Tests: Uses `pytest` and FastAPI `TestClient`. Tests create/drop tables using SQLAlchemy metadata (see `app/tests/conftest.py`). To run tests locally (inside the same environment where `DATABASE_URL` points to a test Postgres instance):

```bash
pytest -q
```

Project-specific Conventions
- Dependency injection: prefer FastAPI dependencies `Depends(get_db)` and tenant ID via `Depends(get_tenant_id)`.
- DB patterns: repositories under `app/repos` perform `db.add`/`db.commit()` and return refreshed objects. When modifying DB, follow existing pattern (commit + refresh) rather than implicit session flush.
- Logging: structured, short messages with `tenant_id` and `document_id` included (see `ingest/service.py`). Keep to this format for observability.
- Embeddings batching: use `batched()` helper in `app/ingest/embedder_openai.py` to respect API limits and preserve order.
 - Embeddings batching: use `batched()` helper in `app/ingest/embedder.py` to respect API limits and preserve order.
 - Use `get_embedder()` from `app.ingest.embedder` to obtain the embedder chosen by `EMBEDDER_PROVIDER`.
   - Example usage in `app/ingest/service.py` uses `embedder = get_embedder()` and `batched()`.
 - Embeddings batching: use `batched()` helper in `app/ingest/embedder_openai.py` to respect API limits and preserve order.
 - LLM factory: use `get_llm_client()` from `app/llm/factory.py` (or `from app.llm import get_llm_client`) to obtain a provider-agnostic client.
   Example usage:

```python
from app.llm import get_llm_client, ChatMessage

client = get_llm_client()
resp = client.chat([ChatMessage(role="user", content="Hello")])
```

  - Providers implemented: `app/llm/openai.py` (wraps OpenAI SDK) and `app/llm/stub.py` (local deterministic stub for tests/CI).
  - OpenAI client requires `OPENAI_API_KEY`. The factory respects `DISABLE_EXTERNAL_LLM_CALLS` to block external calls in CI.
- Avoid touching migrations directly unless adding vector index operations; those were created in `alembic/versions` and require careful DB-specific SQL.

Integration Points & External Dependencies
- Postgres + pgvector: models use `pgvector.sqlalchemy.Vector`. Migrations may include vector index setup.
- OpenAI embeddings via `openai` package: `app/ingest/embedder_openai.py` expects `OpenAI(api_key=...)` client and `embeddings.create` returning ordered `resp.data` entries.
- File storage: simple local filesystem path used in `UPLOAD_DIR`. For production, external object storage would be a substitution point (keep `storage_path` semantics).

Files To Reference When Making Changes
- API: `app/api/documents.py` (upload + ingest endpoints)
- Ingest pipeline: `app/ingest/service.py`, `app/ingest/chunking.py`, `app/ingest/extract.py`, `app/ingest/embedder_openai.py`
- DB models: `app/db/models.py`
- Repos: `app/repos/documents.py`, `app/repos/chunks.py`
- Tests: `app/tests/conftest.py`, `app/tests/api/test_documents.py`

Small Implementation Notes / Examples
- Tenant header enforcement example: use `get_tenant_id` dependency in endpoints; returning 400 for missing header.
- Creating a document: `app/api/documents.py:create_document` writes file to `UPLOAD_DIR`, calls `document_repo.create_document` and returns `DocumentCreateResponse`.
- Replacing chunks: `app/repos/chunks.py:replace_chunks_for_document` deletes old version rows and inserts new `Chunk` rows, then commits; it enforces length parity of texts vs embeddings.

When Editing or Extending
- Preserve tenant scoping: every DB query that returns tenant-owned rows should filter by `tenant_id`.
- Prefer adding small, focused repo helpers under `app/repos` for DB changes rather than new ad-hoc queries in handlers.
- Keep ingest pipeline instrumentation (timing logs) when modifying `ingest_document` to keep observability consistent.

What Not To Change Without Extra Care
- `app/db/models.py` column types and constraints: changing types (UUID, Vector) affects migrations and production data.
- Alembic migrations: they include vector index creation and are DB-specific; update only when you understand the migration semantics.
- Test fixtures: `app/tests/conftest.py` assumes `Base.metadata.create_all()` for test schema. If switching to alembic migrations in tests, adapt fixtures accordingly.

If You Need More Context
- Read `README.md` for the project's objectives and quickstart.
- Inspect `alembic/versions` for migration history, especially vector index migrations.

Feedback
- If any section is unclear or missing, tell me which area (e.g., migrations, OpenAI usage, or upload handling) and I'll expand or add examples.
