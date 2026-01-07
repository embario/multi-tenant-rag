#!/usr/bin/env bash
set -euo pipefail

OWNER="embario"
REPO="multi-tenant-rag"

MS1_TITLE="Week 1: End-to-End RAG"
MS2_TITLE="Week 2: Tenancy, ACLs, Evals, Polish"

create () {
  gh issue create --repo "$OWNER/$REPO" \
    --title "$1" \
    --body "$2" \
    --label "$3" \
    --milestone "$4"
}

# Week 1
create "Day 1: Scaffold + Docker + /health" \
$'Set up FastAPI app, Dockerfile, docker-compose (Postgres), and /health endpoint.\n\nAcceptance:\n- docker compose up --build\n- GET /health returns ok' \
"area:infra,area:api,priority:p0" "$MS1_TITLE"

create "Day 2: Schema + Alembic + pgvector" \
$'Define schema: tenants, users, documents, document_acls, chunks. Enable pgvector.\n\nAcceptance:\n- Migrations run\n- vector extension enabled' \
"area:db,priority:p0" "$MS1_TITLE"

create "Day 3: Document upload endpoint" \
$'POST /documents with upload (TXT/MD/PDF) + metadata.\n\nAcceptance:\n- Upload via Swagger\n- Document row created' \
"area:api,area:ingest,priority:p0" "$MS1_TITLE"

create "Day 4: Parsing + normalization" \
$'Implement TXT/MD/PDF parsing and text normalization.\n\nAcceptance:\n- Text extracted correctly' \
"area:ingest,priority:p0" "$MS1_TITLE"

create "Day 5: Chunking" \
$'Chunk text with overlap and persist chunks.\n\nAcceptance:\n- Stable chunk counts\n- Chunks stored' \
"area:ingest,area:db,priority:p0" "$MS1_TITLE"

create "Day 6: Embeddings + retrieval" \
$'Embed chunks and implement pgvector similarity search (tenant scoped).\n\nAcceptance:\n- Top-k retrieval works' \
"area:rag,area:db,priority:p0" "$MS1_TITLE"

create "Day 7: RAG query endpoint" \
$'POST /query: embed question → retrieve → generate answer with citations.\n\nAcceptance:\n- End-to-end RAG works\n- Citations included' \
"area:rag,area:api,priority:p0" "$MS1_TITLE"

# Week 2
create "Day 8: ACL enforcement" \
$'Enforce document ACLs in retrieval.\n\nAcceptance:\n- Unauthorized access denied' \
"area:db,area:rag,priority:p0" "$MS2_TITLE"

create "Day 9: Tenant isolation hardening" \
$'Enforce tenant_id everywhere. Add seed script.\n\nAcceptance:\n- Cross-tenant access blocked' \
"area:db,area:api,priority:p0" "$MS2_TITLE"

create "Day 10: Document versioning + re-ingest" \
$'Add doc versioning and re-ingest path.\n\nAcceptance:\n- Version increments\n- Latest version only' \
"area:db,area:ingest,priority:p1" "$MS2_TITLE"

create "Day 11: Query logging + evals" \
$'Log latency, tokens, cost. Store baseline eval metrics.\n\nAcceptance:\n- Query + eval rows persisted' \
"area:evals,area:db,priority:p0" "$MS2_TITLE"

create "Day 12: Guardrails + fallback" \
$'Token budgets, timeouts, no-context fallback.\n\nAcceptance:\n- Fallback triggers when no context' \
"area:rag,priority:p1" "$MS2_TITLE"

create "Day 13: Recruiter-ready README + docs" \
$'Improve README, add architecture diagram, document failure modes.\n\nAcceptance:\n- New user runs demo in <10 minutes' \
"area:infra,priority:p0" "$MS2_TITLE"

create "Day 14: Demo script + tests" \
$'Add deterministic demo script and minimal tests.\n\nAcceptance:\n- Demo runs cleanly\n- Tests pass' \
"area:infra,priority:p0" "$MS2_TITLE"
