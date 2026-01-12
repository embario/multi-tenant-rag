import logging
from fastapi import FastAPI
from app.api.documents import router as documents_router

logging.basicConfig(level=logging.INFO)
logging.getLogger("pypdf").setLevel(logging.ERROR)
logging.getLogger("pypdf._reader").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI(title="Multi-Tenant RAG")
app.include_router(documents_router)


@app.get("/health")
def health():
    return {"status": "ok"}
