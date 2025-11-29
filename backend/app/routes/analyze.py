# app/routes/analyze.py
import os, httpx, logging
from fastapi import APIRouter, HTTPException
from app.models.analyze_model import AnalyzeRequest
from app.services.prompts_service import load_prompts, build_prompt
from app.services.incident_service import load_incident_types

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/llm/analyze")
async def analyze_incident(payload: AnalyzeRequest):

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Leerer Text übergeben.")

    types = load_incident_types()
    prompts = load_prompts()
    prompt = build_prompt(text, types, prompts)

    base = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model = os.getenv("OLLAMA_MODEL", "gemma:2b")

    url = f"{base}/api/generate"
    ollama_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": -1}
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=ollama_payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error("LLM Fehler: %r", e)
        raise HTTPException(status_code=502, detail="Fehler bei LLM-Anfrage")

    result = data.get("response", "").strip()

    return {
        "status": "ok",
        "result": result,
        "prompt": prompt,
        "model": model,
        "chars_in": len(text)
    }
