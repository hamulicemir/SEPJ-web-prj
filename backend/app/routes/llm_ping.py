# app/routes/llm_ping.py
import os, httpx, logging
from fastapi import APIRouter, HTTPException

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/api/llm/ping")
async def llm_ping():
    base = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    url = f"{base}/api/tags"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
    except Exception as e:
        logger.error("LLM Ping Fehler: %r", e)
        raise HTTPException(status_code=502, detail="Ollama nicht erreichbar")

    return {"ollama": "ok"}
