# app/routes/analyze.py

import os
import httpx
import logging
import json
from fastapi import APIRouter, HTTPException

from app.models.analyze_model import AnalyzeRequest
from app.services.prompts_service import load_prompts, build_prompt
from app.services.incident_service import load_incident_types
from app.services.incident_questions import load_incident_questions
from app.services.incident_questions import load_incident_questions_for_types
from app.services.load_incident_type_mapping import load_incident_type_mapping

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
    classify_prompt = build_prompt(text, incident_types, prompts)

    # -----------------------------------------------------------------------
    # 4) Modell-Konfiguration aus ENV laden
    # -----------------------------------------------------------------------
    base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model_name = os.getenv("OLLAMA_MODEL", "gemma:2b")

    # -----------------------------------------------------------------------
    # 5) Anfrage an Ollama schicken
    # -----------------------------------------------------------------------
    try:
        result = await call_ollama(model_name, base_url, classify_prompt)
    except Exception as e:
        logger.error("LLM Fehler: %r", e)
        raise HTTPException(status_code=502, detail="Fehler bei LLM-Anfrage")
    
    final_prompt = classify_prompt + f"\nAntwort: {result}"

    # -----------------------------------------------------------------------
    # LLM-Antwort parsen
    # -----------------------------------------------------------------------
    try: 
        llm_raw_list = json.loads(result)
        if not isinstance(llm_raw_list, list):
            raise ValueError("LLM-Antwort ist keine Liste")
    except Exception:
        llm_raw_list = [item.strip() for item in result.split(",")]
        logger.warning("LLM-Antwort konnte nicht als JSON geparst werden, verwende einfache Aufteilung.")
    
    logger.info("LLM-Antwort: %r", llm_raw_list)

    llm_normalized = [item.strip().lower() for item in llm_raw_list]

    # -----------------------------------------------------------------------
    # DB Mapping
    # -----------------------------------------------------------------------
    name_to_code = load_incident_type_mapping()
    logger.info("Name to Code Mapping: %r", name_to_code)

    matched_incidents = []
    for name in llm_normalized:
        if name == "keiner":
            continue
        if name not in name_to_code:
            logger.warning("Unbekannter Vorfalltyp vom LLM: %s", name)
            continue
        code = name_to_code[name]
        matched_incidents.append(code)
    logger.info("Gemappte Vorfalltypen: %r", matched_incidents)

    if not matched_incidents:
        logger.info("Kein bekannter Vorfalltyp erkannt, setze auf 'unknown'")
        matched_incidents.append({"unknown": "unknown"})

    # -----------------------------------------------------------------------
    # 6) Vorfallfragen laden
    # -----------------------------------------------------------------------
    incident_questions = load_incident_questions_for_types(matched_incidents)
    logger.info("Loaded %d incident questions", len(incident_questions))
    logger.info("Questions: %r", incident_questions)

    
    # -----------------------------------------------------------------------
    # 7) LLM Aufruf pro Vorfall
    # -----------------------------------------------------------------------
    answers = {}
    for q in incident_questions:
        question_text = q["label"]
        
        prompt = f"""
        Text: {text}
        Frage: {question_text}
        Regel: Beantworte die Fragen mit kurzen und klaren Antworten. Wenn die Information im Text nicht vorhanden ist, antworte mit 'Keine Information'.
        """

        try:
            llm_answer = await call_ollama(model_name, base_url, prompt)
        except Exception as e:
            logger.error("LLM Fehler bei Frage '%s': %r", question_text, e)
            llm_answer = "Fehler bei der LLM-Anfrage"
            
        logger.info("Frage: %s | Antwort: %s", question_text, llm_answer)
        answers[question_text] = llm_answer

        final_prompt += f"\nFrage: {question_text}\nAntwort: {llm_answer}"

    # -----------------------------------------------------------------------
    # 8) Antwort ans Frontend zurückgeben
    # -----------------------------------------------------------------------
    return {
        "status": "ok",
        "result": result,
        "prompt": final_prompt,
        "model": model_name,
        "chars_in": len(text)
    }
