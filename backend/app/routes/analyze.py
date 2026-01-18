import os
import httpx
import logging
import json
import time
import re
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

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

# helper function: robust JSON extraction (handles markdown blocks)
def extract_json_object(text: str) -> dict:
    try:
        # 1. try direct parse
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. try removing markdown code blocks (e.g. ```json ... ```)
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. try finding the first '{' and last '}'
    try:
        start_index = text.find('{')
        end_index = text.rfind('}')
        if start_index != -1 and end_index != -1:
            json_str = text[start_index : end_index + 1]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
        
    return {}

# helper function: request to ollama (async with metadata)
async def call_ollama_with_meta(model: str, base_url: str, prompt: str) -> tuple[str, dict]:
    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": -1},
        "temperature": 0.2 # Low temp for precision
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        text = data.get("response", "").strip()
        return text, data

# helper function: simple request
async def call_ollama(model: str, base_url: str, prompt: str) -> str:
    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": -1},
        "temperature": 0.2
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

# main endpoint
@router.post("/api/llm/analyze")
async def analyze_incident(payload: AnalyzeRequest, db: Session = Depends(get_db)):

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text provided.")

    logger.info("ANALYZE START")
    logger.info("Input text: %s", text)
    
    # 1. create raw report entry
    raw_report = create_raw_report(
        db,
        text=text,
        title=getattr(payload, "title", None) or "Automatischer Bericht",
        source="api/llm/analyze",
        language="de",
        created_by=None,
    )

    # 2. load config & prompts
    incident_types = load_incident_types()
    prompts = load_prompts()
    
    base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:7b") 

    # 3. classification step
    classify_prompt = build_prompt(text, incident_types, prompts)
    final_prompt = classify_prompt

    try:
        start_ts = time.time()
        result, result_raw = await call_ollama_with_meta(model_name, base_url, classify_prompt)
        latency_ms = int((time.time() - start_ts) * 1000)
    except Exception as e:
        logger.error("LLM Error (classify): %r", e)
        raise HTTPException(status_code=502, detail="Error during LLM classification")
    
    final_prompt += f"\nAnswer: {result}"
    
    # save classification run
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

    # parsing the classifications from LLM response
    try:
        llm_raw_list = json.loads(result)
        if not isinstance(llm_raw_list, list): raise ValueError
    except:
        # fallback if json parse fails
        llm_raw_list = [x.strip() for x in result.split(",") if x.strip()]

    llm_normalized = [x.lower().strip() for x in llm_raw_list]
    name_to_code = load_incident_type_mapping()
    
    matched_incidents = []
    for name in llm_normalized:
        if name == "keiner": continue
        if name in name_to_code:
            matched_incidents.append(name_to_code[name])

    if not matched_incidents:
        matched_incidents = ["unknown"]

    # create incidents in db 
    incident_rows = create_incidents_for_types(db, report_id=raw_report.id, incident_types=matched_incidents)
    type_to_incident = {inc.incident_type: inc for inc in incident_rows}

    # 4. generate detailed questions (parallel execution)
    incident_questions = load_incident_questions_for_types(matched_incidents)
    answers = {}
    tasks = []
    metadata_list = []

    for q in incident_questions:
        inc_type = q["incident_type"]
        question_text = q["label"]
        question_key = q["question_key"]
        
        incident_obj = type_to_incident.get(inc_type)
        if not incident_obj: continue

        prompt = f"Text: {text}\nFrage: {question_text}\nRegel: Beantworte kurz und präzise. Wenn keine Info da ist: 'Keine Information'."
        
        metadata_list.append({
            "inc_type": inc_type, "key": question_key, "text": question_text,
            "inc_id": incident_obj.id, "prompt": prompt, "start_ts": time.time()
        })
        tasks.append(call_ollama_with_meta(model_name, base_url, prompt))

    # execute all questions in parallel
    if tasks:
        logger.info(f"Starting {len(tasks)} questions in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
    else:
        results = []

    # process results
    for i, res in enumerate(results):
        meta = metadata_list[i]
        latency = int((time.time() - meta["start_ts"]) * 1000)
        
        if isinstance(res, Exception):
            val = "Error"
            raw = {"error": str(res)}
        else:
            val, raw = res

        answers.setdefault(meta["inc_type"], {})[meta["key"]] = val
        final_prompt += f"\nQuestion: {meta['text']}\nAnswer: {val}"
        
        create_llm_run(db, purpose="extract_answer", model_name=model_name, request_payload={"prompt": meta["prompt"]}, response_payload=raw, report_id=raw_report.id, incident_id=meta["inc_id"], latency_ms=latency)
        create_structured_answer(db, incident_id=meta["inc_id"], question_key=meta["key"], answer_text=val)

    db.commit()

    # summarize extracted facts for the final writer
    facts_summary = ""
    for inc_type, facts in answers.items():
        facts_summary += f"\n[{inc_type.upper()}]\n" + "\n".join([f"- {k}: {v}" for k,v in facts.items()])

    # final report generation - V6 PROMPT (Fluent Style & Robust Metadata)
    writer_prompt = f"""
Du bist ein professioneller Schriftführer im österreichischen Justizvollzug.
Deine Aufgabe: Verfasse einen **fließenden, narrativen** Amtsbericht und extrahiere Metadaten.

INPUT: "{text}"
DETAILS: {facts_summary}

ANWEISUNGEN FÜR DEN TEXT (Body):
1. **Stil:** Schreibe NICHT stichwortartig ("Wurde verlegt."), sondern in ganzen, fließenden Sätzen ("Aufgrund des Vorfalls wurde eine sofortige Verlegung veranlasst.").
2. **Konnektoren:** Verbinde Sätze sinnvoll (z.B. "daraufhin", "anschließend", "im Zuge dessen").
3. **Namen:** Schreibe immer den Titel dazu (z.B. "Insasse Schärdinger").
4. **Vollständigkeit:** Übernimm alle Details, aber vermeide reine Wiederholungen der Einleitung.

BEISPIEL FÜR DEN STIL (One-Shot):
Input: "Ich ging zur Zelle. Da war Rauch."
Output: "Im Zuge des Nachtdienstes begab ich mich zum Haftraum, da aus diesem eine Rauchentwicklung wahrnehmbar war."

ANWEISUNGEN FÜR DIE METADATEN (JSON):
- "meta_place": Nenne den **genauen Ort** aus dem Text (z.B. "Haftraum 1.205").
- "meta_persons": Liste NUR die Insassen.

FORMAT (JSON):
{{
  "meta_date": "Datum des Vorfalls (DD.MM.YYYY)",
  "meta_time": "Uhrzeit (HH:MM)",
  "meta_place": "Genauer Ort",
  "meta_persons": ["Insasse A", "Insasse B"],
  "intro": "Einleitung: Wer meldet den Vorfall?",
  "main": "Sachverhalt: Fließender Text.",
  "measures": "Maßnahmen: Fließender Text."
}}

Gib NUR das JSON zurück.
"""
    
    final_report_structure = {}
    try:
        start_ts = time.time()
        
        # llm request
        final_report_text_raw = await call_ollama(model_name, base_url, writer_prompt)
        latency_ms = int((time.time() - start_ts) * 1000)

        # parse json 
        report_parts = extract_json_object(final_report_text_raw)
        
        if not report_parts: 
            logger.error("JSON Parsing failed. Raw text: %s", final_report_text_raw)
            report_parts = {"intro": "Fehler.", "main": final_report_text_raw, "measures": ""}

        # extract reporter name via regex
        reporter = "System (AI)"
        match_rep = re.search(r'(?:Hier spricht|Ich bin|Meldung von)\s+([A-Za-zäöüÄÖÜß]+)', text)
        if match_rep: reporter = match_rep.group(1)

        # 1. Report Date
        report_creation_date = datetime.now().strftime('%d.%m.%Y')

        # 2. Incident Metadata extraction with FALLBACK logic
        # Date
        incident_date = report_parts.get("meta_date")
        if not incident_date or incident_date == "-": incident_date = report_creation_date
        
        # Place - FALLBACK: If Writer missed it, look in Q&A answers
        incident_place = report_parts.get("meta_place")
        if not incident_place or incident_place in ["-", ""]:
            # Fallback: Search in answers for keys like "location", "place", "wo"
            for inc_type, facts in answers.items():
                for k, v in facts.items():
                    if "wo" in k.lower() or "place" in k.lower() or "ort" in k.lower():
                        incident_place = v
                        break
                if incident_place and incident_place not in ["-", ""]: break
        if not incident_place: incident_place = "-"

        # Time
        incident_time = report_parts.get("meta_time", "-")
        
        # 3. Persons list
        raw_persons = report_parts.get("meta_persons", [])
        if isinstance(raw_persons, list):
            final_accused = raw_persons
        elif isinstance(raw_persons, str):
            final_accused = [p.strip() for p in raw_persons.split(",")]
        else:
            final_accused = []

        # construct final structure
        final_report_structure = {
            "data": {
                "filename": "upload.txt", 
                "text": text,
                "notes": []
            },
            "annotations": {
                "report_date": report_creation_date, 
                "reporter": reporter,
                "reported_to": "Inspektionsdienst",
                
                # Metadata Table
                "place": incident_place,
                "date": incident_date,
                "time": incident_time,
                "accused": final_accused,
                
                "colleagues": [],
                "other_attendees": [],
                "incidents": [
                    {
                        "structure": "Einleitung",
                        "type": "N/A",
                        "text": report_parts.get("intro", "") 
                    },
                    {
                        "structure": "Sachverhalt",
                        "type": ", ".join(matched_incidents),
                        "type_details": answers,
                        "text": report_parts.get("main", "")
                    },
                    {
                        "structure": "Maßnahmen",
                        "type": "N/A",
                        "text": report_parts.get("measures", "") 
                    }
                ]
            }
        }
        
        # save final report
        if incident_rows:
            primary = incident_rows[0]
            final_rep = FinalReport(incident_id=primary.id, body_md=json.dumps(final_report_structure, ensure_ascii=False), model_name=model_name)
            db.add(final_rep)
            db.commit()
            create_llm_run(db, purpose="write_final_report_json", model_name=model_name, request_payload={"prompt": writer_prompt}, response_payload={"response": final_report_structure}, report_id=raw_report.id, incident_id=primary.id, latency_ms=latency_ms)

    except Exception as e:
        logger.error(f"Error write report: {e}")
        final_report_structure = {"error": str(e)}

    return {
        "status": "ok", "final_report": final_report_structure, "model": model_name,
        "raw_report_id": str(raw_report.id), "matched_incident_types": matched_incidents
    }