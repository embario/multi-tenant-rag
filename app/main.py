from fastapi import FastAPI

app = FastAPI(title="Multi-Tenant RAG")

@app.get("/health")
def health():
    return {"status": "ok"}