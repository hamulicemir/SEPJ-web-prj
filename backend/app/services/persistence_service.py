import time
from typing import Iterable, List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.db_models import RawReport, Incident, StructuredAnswer, LLMRun


def create_raw_report(
    db: Session,
    *,
    text: str,
    title: Optional[str] = None,
    source: str = "api",
    language: str = "de",
    created_by: Optional[str] = None,
) -> RawReport:
    report = RawReport(
        title=title,
        body=text,
        language=language,
        source=source,
        created_by=created_by,
    )
    db.add(report)
    db.flush()  # damit report.id gesetzt ist
    return report


def create_incidents_for_types(
    db: Session,
    *,
    report_id,
    incident_types: Iterable[str],
) -> List[Incident]:
    incidents: List[Incident] = []
    for code in incident_types:
        inc = Incident(
            report_id=report_id,
            incident_type=code,
            status="new",
        )
        db.add(inc)
        db.flush()
        incidents.append(inc)
    return incidents


def create_llm_run(
    db: Session,
    *,
    purpose: str,
    model_name: str,
    request_payload: Dict[str, Any],
    response_payload: Dict[str, Any],
    report_id=None,
    incident_id=None,
    latency_ms: Optional[int] = None,
) -> LLMRun:
    tokens_prompt = None
    tokens_completion = None

    # Optional: typische Felder von Ollama, nur wenn vorhanden
    if isinstance(response_payload, dict):
        tokens_prompt = response_payload.get("prompt_eval_count")
        tokens_completion = response_payload.get("eval_count")

    run = LLMRun(
        purpose=purpose,
        report_id=report_id,
        incident_id=incident_id,
        model_name=model_name,
        request_json=request_payload,
        response_json=response_payload,
        tokens_prompt=tokens_prompt,
        tokens_completion=tokens_completion,
        latency_ms=latency_ms,
    )
    db.add(run)
    db.flush()
    return run


def create_structured_answer(
    db: Session,
    *,
    incident_id,
    question_key: str,
    answer_text: str,
) -> StructuredAnswer:
    sa = StructuredAnswer(
        incident_id=incident_id,
        question_key=question_key,
        value_json={"answer": answer_text},
    )
    db.add(sa)
    db.flush()
    return sa
