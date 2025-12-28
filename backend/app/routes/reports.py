from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.models.db_models import RawReport, LLMRun, FinalReport
import json
import re

router = APIRouter()

def clean_llm_response(response_data):
    """
    Hilfsfunktion: Holt den reinen Text aus verschiedenen Antwort-Formaten.
    """
    if not response_data:
        return ""
    
    if isinstance(response_data, dict):
        return response_data.get("response", str(response_data))
    
    if isinstance(response_data, str):
        return response_data
        
    return str(response_data)

def parse_classification(response_data):
    """
    Versucht, eine Klassifikations-Liste aus den Daten zu retten.
    """
    try:
        if isinstance(response_data, list):
            return response_data
            
        text = clean_llm_response(response_data)
        
        if "[" in text and "]" in text:
            try:
                match = re.search(r'\[.*\]', text, re.DOTALL)
                if match:
                    json_str = match.group(0).replace("'", '"') # Fix single quotes
                    return json.loads(json_str)
            except:
                pass
                
        if len(text) < 50:
            return [text]
            
        return []
    except:
        return []

@router.get("/api/reports/history")
def get_reports_history(limit: int = 20, db: Session = Depends(get_db)):
    reports = db.query(RawReport).order_by(desc(RawReport.created_at)).limit(limit).all()
    
    history_data = []
    
    for r in reports:
        runs = db.query(LLMRun).filter(LLMRun.report_id == r.id).order_by(LLMRun.created_at).all()
        
        final_rep_entry = db.query(FinalReport).filter(FinalReport.incident_id.in_(
            [run.incident_id for run in runs if run.incident_id]
        )).first()

        classification = []
        facts = {}
        
        for run in runs:
            try:
                if run.purpose == "classify":
                    classification = parse_classification(run.response_json)
                
                elif run.purpose == "extract_answer" and run.request_json:
                    answ = clean_llm_response(run.response_json)
                    
                    prompt_snippet = run.request_json.get("prompt", "")
                    if "Frage:" in prompt_snippet:
                        label = prompt_snippet.split("Frage:")[-1].split("\n")[0].strip()
                        facts[label] = answ
            except Exception as e:
                print(f"Error parsing run {run.id}: {e}")
                continue

        # Final Report Body laden
        final_report_content = None
        if final_rep_entry:
            try:
                final_report_content = json.loads(final_rep_entry.body_md)
            except:
                final_report_content = final_rep_entry.body_md

        history_data.append({
            "id": str(r.id),
            "title": r.title or "Unbenannter Bericht",
            "date": r.created_at,
            "preview": r.body[:60] + "..." if r.body else "",
            "full_text": r.body,
            "result_data": {
                "classification": classification,
                "facts": facts,
                "final_report": final_report_content
            }
        })
    
    return history_data