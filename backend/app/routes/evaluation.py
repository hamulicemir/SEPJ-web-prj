import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.models.db_models import FinalReport, Incident 
from app.services.evaluation_service import calculate_metrics

router = APIRouter()
logger = logging.getLogger(__name__)

def parse_report_data(report_body: str):
    """Extracts narrative text and metadata facts from the stored JSON report."""
    try:
        data = json.loads(report_body)
        narrative_parts = []
        annotations = data.get("annotations", {})
        
        # Extract main text
        incidents = annotations.get("incidents", [])
        for inc in incidents:
            if inc.get("text"):
                narrative_parts.append(inc["text"])
        
        full_text = "\n".join(narrative_parts)
        if not full_text: 
            full_text = data.get("data", {}).get("text", "")

        # Extract structured facts for metric calculation
        facts = {
            "meta_persons": annotations.get("accused", []) or annotations.get("meta_persons", []),
            "meta_place": annotations.get("place", "") or annotations.get("meta_place", ""),
            "meta_time": annotations.get("time", "") or annotations.get("meta_time", ""),
            "meta_date": annotations.get("date", "") or annotations.get("meta_date", "")
        }
        return full_text, facts
    except Exception as e:
        logger.error(f"Error parsing report JSON: {e}")
        return "", {}

def get_report_flexible(db: Session, lookup_id: UUID):
    """
    Attempts to find a FinalReport using three strategies:
    1. Direct FinalReport ID
    2. Incident ID
    3. RawReport ID (via Incident join)
    """
    # Strategy 1: ID matches FinalReport.id
    rep = db.query(FinalReport).filter(FinalReport.id == lookup_id).first()
    if rep: return rep
    
    # Strategy 2: ID matches Incident.id
    rep = db.query(FinalReport).filter(FinalReport.incident_id == lookup_id).first()
    if rep: return rep
    
    # Strategy 3: ID matches RawReport.id (Frontend usually sends this)
    rep = db.query(FinalReport).join(Incident).filter(Incident.report_id == lookup_id).first()
    return rep

@router.post("/api/eval/set-reference/{report_id}")
def set_reference_report(report_id: UUID, db: Session = Depends(get_db)):
    """Toggles the 'is_reference' flag for the specified report."""
    report = get_report_flexible(db, report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Toggle logic: Switch between True and False
    report.is_reference = not report.is_reference
    db.commit()
    
    status_msg = "set" if report.is_reference else "removed"
    
    return {
        "status": "ok", 
        "message": f"Report reference {status_msg}",
        "is_reference": report.is_reference
    }

@router.post("/api/eval/compare")
def compare_reports(
    payload: dict = Body(...), 
    db: Session = Depends(get_db)
):
    """
    Calculates metrics (ROUGE, Levenshtein, Facts) between two reports.
    """
    candidate_id = payload.get("candidate_id")
    reference_id = payload.get("reference_id")

    if not candidate_id or not reference_id:
        raise HTTPException(status_code=400, detail="Missing IDs")

    # Resolve both IDs flexibly
    cand_rep = get_report_flexible(db, candidate_id)
    ref_rep = get_report_flexible(db, reference_id)

    if not cand_rep or not ref_rep:
        raise HTTPException(status_code=404, detail="One or both reports not found")

    # Parse content
    cand_text, cand_facts = parse_report_data(cand_rep.body_md)
    ref_text, ref_facts = parse_report_data(ref_rep.body_md)

    # Run comparison logic
    metrics = calculate_metrics(
        generated_text=cand_text,
        reference_text=ref_text,
        generated_facts=cand_facts,
        reference_facts=ref_facts
    )

    return {
        "candidate_id": str(candidate_id),
        "reference_id": str(reference_id),
        "metrics": metrics
    }