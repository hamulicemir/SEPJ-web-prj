# app/services/incident_questions.py
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.db.session import engine
import logging
import uuid

# Imports für CRUD
from app.models.db_models import IncidentQuestion
from app.models.analyze_model import QuestionBase, QuestionUpdate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ALT: Bestehende Funktionen für den Analyze-Endpoint (Raw SQL)
# ---------------------------------------------------------------------------

def load_incident_questions():
    try:
        with engine.connect() as conn:
            rows = conn.execute(sa.text(
                "SELECT incident_type, question_key, label, answer_type, order_index FROM incident_questions ORDER BY incident_type, order_index"
            )).fetchall()

        # Achtung: im Original hattest du einmal "questions_key" und einmal "question_key". 
        # Ich habe es auf "question_key" standardisiert, passend zum DB Model.
        return [
            {
                "incident_type": r[0],
                "question_key": r[1],
                "label": r[2],
                "answer_type": r[3],
                "order_index": r[4],
            }
            for r in rows
        ]

    except Exception as e:
        logger.warning("Fehler beim Laden der Incident Questions %r", e)
        return []

def load_incident_questions_for_types(types: list[str]):
    if not types:
        return []

    # Mapping verwenden, damit Column-Namen stimmen
    query = sa.text("""
        SELECT incident_type, question_key, label, answer_type, order_index
        FROM incident_questions
        WHERE incident_type = ANY(:types)
        ORDER BY incident_type, order_index
    """)

    with engine.connect() as conn:
        # mappings() erlaubt Zugriff per Spaltenname
        rows = conn.execute(query, {"types": types}).mappings().fetchall()

    return [
        {
            "incident_type": r["incident_type"],
            "question_key": r["question_key"],
            "label": r["label"],
            "answer_type": r["answer_type"],
            "order_index": r["order_index"],
        }
        for r in rows
    ]

# ---------------------------------------------------------------------------
# NEU: CRUD Funktionen für Admin-Dashboard (ORM)
# ---------------------------------------------------------------------------

def get_all_questions(db: Session):
    return db.query(IncidentQuestion).order_by(IncidentQuestion.incident_type, IncidentQuestion.order_index).all()

def create_question(db: Session, data: QuestionBase):
    obj = IncidentQuestion(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_question(db: Session, q_id: uuid.UUID, data: QuestionUpdate):
    obj = db.query(IncidentQuestion).filter(IncidentQuestion.id == q_id).first()
    if obj:
        # Nur Felder updaten die gesetzt sind
        update_data = data.dict(exclude_unset=True)
        for key, val in update_data.items():
            setattr(obj, key, val)
        db.commit()
        db.refresh(obj)
    return obj

def delete_question(db: Session, q_id: uuid.UUID):
    obj = db.query(IncidentQuestion).filter(IncidentQuestion.id == q_id).first()
    if obj:
        db.delete(obj)
        db.commit()
        return True
    return False