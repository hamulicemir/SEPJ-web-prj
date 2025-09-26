from fastapi import FastAPI
from .db import engine
import sqlalchemy as sa
import os, httpx

app = FastAPI(title="SEPJ API")

@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(sa.text("SELECT 1"))
    return {"status": "ok"}

@app.get("/api/hello")
def hello():
    return {"msg": "Hello from FastAPI."}

@app.get("/api/llm/ping")
async def llm_ping():
    base = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{base}/api/tags")
        r.raise_for_status()
    return {"ollama": "ok"}
