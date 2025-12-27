# app/routes/analyze.py

import os
import httpx
import logging
import json
import time
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.analyze_model import AnalyzeRequest
from app.services.prompts_service import load_prompts, build_prompt
from app.services.incident_service import load_incident_types
from app.services.incident_questions import load_incident_questions
from app.services.incident_questions import load_incident_questions_for_types
from app.services.load_incident_type_mapping import load_incident_type_mapping
from app.db.session import get_db
from app.models.db_models import RawReport, Incident, StructuredAnswer, LLMRun, FinalReport
from app.services.persistence_service import (
    create_raw_report,
    create_incidents_for_types,
    create_llm_run,
    create_structured_answer,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hilfsfunktion: Anfrage an Ollama / Local LLM
# ---------------------------------------------------------------------------
async def call_ollama_with_meta(model: str, base_url: str, prompt: str) -> tuple[str, dict]:
    """
    Sendet einen Prompt an Ollama und gibt (Antworttext, komplette JSON-Response) zurück.
    """
    url = f"{base_url}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": -1},
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        text = data.get("response", "").strip()
        return text, data
    
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
async def analyze_incident(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    # -----------------------------------------------------------------------
    # 1) Eingabetext prüfen & speichern
    # -----------------------------------------------------------------------
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Leerer Text übergeben.")

    logger.info("ANALYZE START")
    logger.info("Input text: %s", text)

    raw_report = create_raw_report(
        db,
        text=text,
        title=getattr(payload, "title", None) or "Automatischer Bericht",
        source="api/llm/analyze",
        language="de",
        created_by=None,
    )
    logger.info("Raw report gespeichert: %s", raw_report.id)

    # -----------------------------------------------------------------------
    # 2) Typen & Promptfragmente laden
    # -----------------------------------------------------------------------
    incident_types = load_incident_types()
    prompts = load_prompts()

    # -----------------------------------------------------------------------
    # 3) Klassifikations-Prompt bauen
    # -----------------------------------------------------------------------
    classify_prompt = build_prompt(text, incident_types, prompts)
    logger.info("Generated classify prompt:\n%s", classify_prompt)
    final_prompt = classify_prompt

    # -----------------------------------------------------------------------
    # 4) Konfiguration
    # -----------------------------------------------------------------------
    base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model_name = os.getenv("OLLAMA_MODEL", "gemma:2b")

    # -----------------------------------------------------------------------
    # 5) Klassifikation an LLM senden
    # -----------------------------------------------------------------------
    try:
        start_ts = time.time()
        result, result_raw = await call_ollama_with_meta(model_name, base_url, classify_prompt)
        latency_ms = int((time.time() - start_ts) * 1000)
    except Exception as e:
        logger.error("LLM Fehler (classify): %r", e)
        raise HTTPException(status_code=502, detail="Fehler bei LLM-Anfrage (classify)")
    
    final_prompt += f"\nAntwort: {result}"

    logger.info("LLM raw classification response: %s", result_raw)
    logger.info("LLM classification text response: %s", result)

    # Save classify run
    create_llm_run(
        db,
        purpose="classify",
        model_name=model_name,
        request_payload={"prompt": classify_prompt},
        response_payload=result_raw,
        report_id=raw_report.id,
        incident_id=None,
        latency_ms=latency_ms,
    )

    # -----------------------------------------------------------------------
    # 6) Klassifikationsergebnis parsen
    # -----------------------------------------------------------------------
    logger.info("Attempting JSON parse of LLM response: %s", result)

    try:
        llm_raw_list = json.loads(result)
        if not isinstance(llm_raw_list, list):
            raise ValueError("LLM Antwort ist keine Liste")
    except Exception:
        llm_raw_list = [x.strip() for x in result.split(",") if x.strip()]
        logger.warning("JSON parse failed. Fallback aktiviert: %s", llm_raw_list)

    logger.info("LLM-Antwort (raw list): %r", llm_raw_list)

    llm_normalized = [x.lower().strip() for x in llm_raw_list]
    logger.info("LLM normalized list: %s", llm_normalized)

    # -----------------------------------------------------------------------
    # 7) Mapping von Text zu Code
    # -----------------------------------------------------------------------
    name_to_code = load_incident_type_mapping()
    logger.info("Loaded name_to_code mapping: %s", name_to_code)

    matched_incidents = []
    for name in llm_normalized:
        logger.info("Checking LLM result: '%s'", name)

        if name == "keiner":
            continue

        if name not in name_to_code:
            logger.warning("Unbekannter Vorfalltyp: %s", name)
            continue

        matched_incidents.append(name_to_code[name])
        logger.info("Mapped '%s' → '%s'", name, name_to_code[name])

    logger.info("Matched incidents: %s", matched_incidents)

    if not matched_incidents:
        logger.warning("Keine Vorfälle erkannt → fallback: unknown")
        matched_incidents = ["unknown"]

    # -----------------------------------------------------------------------
    # 8) Incidents erstellen
    # -----------------------------------------------------------------------
    incident_rows = create_incidents_for_types(
        db,
        report_id=raw_report.id,
        incident_types=matched_incidents,
    )

    type_to_incident = {inc.incident_type: inc for inc in incident_rows}

    # -----------------------------------------------------------------------
    # 9) Fragen zu Vorfalltypen laden
    # -----------------------------------------------------------------------
    incident_questions = load_incident_questions_for_types(matched_incidents)
    logger.info("Loaded %d incident questions", len(incident_questions))
    logger.info("Questions: %r", incident_questions)

    # -----------------------------------------------------------------------
    # 10) Fragen an LLM pro Incident
    # -----------------------------------------------------------------------
    answers = {}

    for q in incident_questions:
        inc_type = q["incident_type"]
        question_text = q["label"]
        question_key = q["question_key"]

        incident_obj = type_to_incident.get(inc_type)
        if incident_obj is None:
            logger.warning("Keine Incident-Instanz für %s gefunden", inc_type)
            continue

        # Prompt erst jetzt definieren!
        prompt = f"""
Text: {text}
Frage: {question_text}
Regel: Beantworte die Frage klar und knapp. Wenn keine Information im Text steht, antworte 'Keine Information'.
"""

        logger.info("Generated question prompt for type=%s:\n%s", inc_type, prompt)

        # LLM Call
        try:
            start_ts = time.time()
            llm_answer, llm_raw = await call_ollama_with_meta(model_name, base_url, prompt)
            latency_ms = int((time.time() - start_ts) * 1000)
        except Exception as e:
            logger.error("LLM Fehler bei Frage '%s': %r", question_text, e)
            llm_answer = "Fehler bei der LLM-Anfrage"
            llm_raw = {"error": str(e)}
            latency_ms = None

        logger.info("Antwort erhalten: %s → %s", question_key, llm_answer)

        answers.setdefault(inc_type, {})[question_key] = llm_answer
        final_prompt += f"\nFrage: {question_text}\nAntwort: {llm_answer}"
        
        # Save LLM run
        create_llm_run(
            db,
            purpose="extract_answer",
            model_name=model_name,
            request_payload={"prompt": prompt},
            response_payload=llm_raw,
            report_id=raw_report.id,
            incident_id=incident_obj.id,
            latency_ms=latency_ms,
        )

        # Save structured answer
        create_structured_answer(
            db,
            incident_id=incident_obj.id,
            question_key=question_key,
            answer_text=llm_answer,
        )

    db.commit()

    # ... (Dein Code nach dem Loop über die Fragen und db.commit() ...)

    # -----------------------------------------------------------------------
    # 11) Formalen Bericht generieren
    # -----------------------------------------------------------------------
    logger.info("Generiere formalen Abschlussbericht...")

    # A) Fakten für den Prompt zusammenfassen (String bauen)
    facts_summary = ""
    for inc_type, facts in answers.items():
        facts_summary += f"\n[Vorfall: {inc_type.upper()}]\n"
        for key, value in facts.items():
            facts_summary += f"- {key}: {value}\n"

    # B) Der Prompt für den Schreiber
    # Wir nutzen strict den existierenden Stil: F-String mit Kontext.
    writer_prompt = f"""
Du bist ein Polizeibeamter. Schreibe einen formalen, sachlichen Bericht (Fließtext) basierend auf dem folgenden Sachverhalt und den extrahierten Fakten.

Original-Text:
"{text}"

Bestätigte Fakten:
{facts_summary}

Anweisungen:
- Schreibe im passiven Beamtendeutsch (z.B. "wurde festgestellt", "ereignete sich").
- Fasse das Geschehen chronologisch zusammen.
- Erwähne alle beteiligten Personen und Zeiten.
- Keine Aufzählungszeichen, nur Fließtext.
"""

    final_report_text = ""
    
    try:
        start_ts = time.time()
        
        # Wir nutzen die existierende Funktion call_ollama (gibt nur Text zurück)
        # Falls du Meta-Daten willst, nimm call_ollama_with_meta (wie oben)
        final_report_text = await call_ollama(model_name, base_url, writer_prompt)
        
        latency_ms = int((time.time() - start_ts) * 1000)

        # C) Speichern in der DB (FinalReport)
        # Wir verknüpfen den Bericht mit dem ersten gefundenen Incident (Haupt-Delikt)
        if incident_rows:
            primary_incident = incident_rows[0]
            
            final_rep_entry = FinalReport(
                incident_id=primary_incident.id,
                body_md=final_report_text,
                model_name=model_name,
                created_by=None 
            )
            db.add(final_rep_entry)
            db.commit()
            
            logger.info("Final Report gespeichert: %s", final_rep_entry.id)

            # D) Auch diesen Schritt loggen (Konsistenz wahren!)
            create_llm_run(
                db,
                purpose="write_final_report",
                model_name=model_name,
                request_payload={"prompt": writer_prompt},
                response_payload={"response": final_report_text},
                report_id=raw_report.id,
                incident_id=primary_incident.id,
                latency_ms=latency_ms,
            )

    except Exception as e:
        logger.error("Fehler bei der Berichts-Generierung: %r", e)
        final_report_text = "Fehler: Bericht konnte nicht generiert werden."

    # -----------------------------------------------------------------------
    # 12) Antwort zurückgeben
    # -----------------------------------------------------------------------
    return {
        "status": "ok",
        "result": result,
        "final_report": final_report_text,
        "prompt": final_prompt,
        "model": model_name,
        "chars_in": len(text),
        "raw_report_id": str(raw_report.id),
        "incident_ids": [str(i.id) for i in incident_rows],
        "matched_incident_types": matched_incidents,
        "answers": answers,
    }
