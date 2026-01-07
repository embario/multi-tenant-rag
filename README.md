# Multi-Tenant RAG

Production-style Retrieval-Augmented Generation service built with:

- Python + FastAPI
- PostgreSQL + pgvector
- Multi-tenant isolation
- Permission-aware retrieval (ACLs)
- RAG answers with citations
- Query logging (latency, tokens, cost)
- Baseline automated evals

## Quickstart
1. Install Docker + Docker Compose
2. Copy `.env.example` to `.env`
3. Run:
   docker compose up --build
4. Open: http://localhost:8000/docs

## Scope
This project intentionally prioritizes:
- correctness
- isolation
- observability
over UI polish.

See GitHub Issues for the full build plan.
EOF