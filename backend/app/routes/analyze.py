# app/routes/analyze.py

import os
import httpx
import logging
from fastapi import APIRouter, HTTPException

from app.models.analyze_model import AnalyzeRequest
from app.services.prompts_service import load_prompts, build_prompt
from app.services.incident_service import load_incident_types

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Hilfsfunktion: Anfrage an Ollama / Local LLM
# ---------------------------------------------------------------------------
async def call_ollama(model: str, base_url: str, prompt: str) -> str:
    """Sendet einen Prompt an Ollama und gibt den Text der Antwort zurück."""
    url = f"{base_url}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": -1}
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()


# ---------------------------------------------------------------------------
# Haupt-Endpoint: Incident-Analyse
# ---------------------------------------------------------------------------
@router.post("/api/llm/analyze")
async def analyze_incident(payload: AnalyzeRequest):
 
    # -----------------------------------------------------------------------
    # 1) Eingabetext prüfen
    # -----------------------------------------------------------------------
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Leerer Text übergeben.")

    # -----------------------------------------------------------------------
    # 2) Vorfallstypen + Promptfragmente laden
    # -----------------------------------------------------------------------
    incident_types = load_incident_types()
    prompts = load_prompts()

    # -----------------------------------------------------------------------
    # 3) Finalen LLM-Prompt bauen
    # -----------------------------------------------------------------------
    final_prompt = build_prompt(text, incident_types, prompts)

    # -----------------------------------------------------------------------
    # 4) Modell-Konfiguration aus ENV laden
    # -----------------------------------------------------------------------
    base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model_name = os.getenv("OLLAMA_MODEL", "gemma:2b")

    # -----------------------------------------------------------------------
    # 5) Anfrage an Ollama schicken
    # -----------------------------------------------------------------------
    try:
        result = await call_ollama(model_name, base_url, final_prompt)
    except Exception as e:
        logger.error("LLM Fehler: %r", e)
        raise HTTPException(status_code=502, detail="Fehler bei LLM-Anfrage")

    # -----------------------------------------------------------------------
    # 6) Antwort ans Frontend zurückgeben
    # -----------------------------------------------------------------------
    return {
        "status": "ok",
        "result": result,
        "prompt": final_prompt,
        "model": model_name,
        "chars_in": len(text)
    }
