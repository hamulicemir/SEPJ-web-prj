from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from difflib import SequenceMatcher
import uuid

from app.db.session import get_db
from app.models.db_models import LLMRun
# Wir nutzen die neuen Models, die wir gefixt haben
from app.models.analyze_model import (
    PromptOut, PromptBase, PromptUpdate,
    IncidentTypeOut, IncidentTypeCreate, IncidentTypeUpdate,
    QuestionOut, QuestionBase, QuestionUpdate,
    LLMRunOut, MetricRequest
)
# Wir importieren die Services, die du gerade aktualisiert hast
from app.services import prompts_service, incident_service, incident_questions

router = APIRouter(tags=["Admin"])

# --- PROMPTS CRUD ---
@router.get("/api/prompts/", response_model=List[PromptOut])
def list_prompts(db: Session = Depends(get_db)):
    return prompts_service.get_all_prompts(db)

@router.post("/api/prompts/", response_model=PromptOut)
def create_prompt(data: PromptBase, db: Session = Depends(get_db)):
    return prompts_service.create_prompt(db, data)

@router.put("/api/prompts/{prompt_id}", response_model=PromptOut)
def update_prompt(prompt_id: uuid.UUID, data: PromptUpdate, db: Session = Depends(get_db)):
    res = prompts_service.update_prompt(db, prompt_id, data)
    if not res: raise HTTPException(404, "Prompt not found")
    return res

@router.delete("/api/prompts/{prompt_id}")
def delete_prompt(prompt_id: uuid.UUID, db: Session = Depends(get_db)):
    if not prompts_service.delete_prompt(db, prompt_id): raise HTTPException(404, "Not found")
    return {"status": "deleted"}

# --- INCIDENT TYPES CRUD ---
@router.get("/api/config/types", response_model=List[IncidentTypeOut])
def get_types(db: Session = Depends(get_db)):
    return incident_service.get_all_types(db)

@router.post("/api/config/types", response_model=IncidentTypeOut)
def create_type(data: IncidentTypeCreate, db: Session = Depends(get_db)):
    res = incident_service.create_type(db, data)
    if not res: raise HTTPException(400, "Code already exists")
    return res

@router.put("/api/config/types/{code}", response_model=IncidentTypeOut)
def update_type(code: str, data: IncidentTypeUpdate, db: Session = Depends(get_db)):
    res = incident_service.update_type(db, code, data)
    if not res: raise HTTPException(404, "Type not found")
    return res

@router.delete("/api/config/types/{code}")
def delete_type(code: str, db: Session = Depends(get_db)):
    if not incident_service.delete_type(db, code): raise HTTPException(404, "Not found")
    return {"status": "deleted"}

# --- QUESTIONS CRUD ---
@router.get("/api/config/questions", response_model=List[QuestionOut])
def get_questions(db: Session = Depends(get_db)):
    return incident_questions.get_all_questions(db)

@router.post("/api/config/questions", response_model=QuestionOut)
def create_question(data: QuestionBase, db: Session = Depends(get_db)):
    return incident_questions.create_question(db, data)

@router.put("/api/config/questions/{q_id}", response_model=QuestionOut)
def update_question(q_id: uuid.UUID, data: QuestionUpdate, db: Session = Depends(get_db)):
    res = incident_questions.update_question(db, q_id, data)
    if not res: raise HTTPException(404, "Question not found")
    return res

@router.delete("/api/config/questions/{q_id}")
def delete_question(q_id: uuid.UUID, db: Session = Depends(get_db)):
    if not incident_questions.delete_question(db, q_id): raise HTTPException(404, "Not found")
    return {"status": "deleted"}

# --- LOGS & METRICS ---
@router.get("/api/logs/runs", response_model=List[LLMRunOut])
def get_llm_runs(limit: int=50, db: Session = Depends(get_db)):
    return db.query(LLMRun).order_by(LLMRun.created_at.desc()).limit(limit).all()

@router.post("/api/metrics/compare")
def compare_texts(payload: MetricRequest):
    ratio = SequenceMatcher(None, payload.text1, payload.text2).ratio()
    return {"similarity_ratio": ratio}