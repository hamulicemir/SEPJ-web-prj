# app/services/incident_service.py
import sqlalchemy as sa
from sqlalchemy.orm import Session
import logging
from app.db.session import engine

# Imports für CRUD
from app.models.db_models import IncidentType
from app.models.analyze_model import IncidentTypeCreate, IncidentTypeUpdate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ALT: Bestehende Funktion für den Analyze-Endpoint (Raw SQL)
# ---------------------------------------------------------------------------

def load_incident_types():
    try:
        with engine.connect() as conn:
            rows = conn.execute(sa.text(
                "SELECT code, name, description FROM incident_types ORDER BY code"
            )).fetchall()

        return [
            {"code": r[0], "name": r[1], "desc": r[2] or ""}
            for r in rows
        ]

    except Exception as e:
        logger.warning("Falling back to default incident types: %r", e)
        fallback = [
            "einbruch", "sachbeschaedigung", "koerperverletzung",
            "brandstiftung", "selbstverletzung"
        ]
        return [{"code": c, "name": c.capitalize(), "desc": ""} for c in fallback]

# ---------------------------------------------------------------------------
# NEU: CRUD Funktionen für Admin-Dashboard (ORM)
# ---------------------------------------------------------------------------

def get_all_types(db: Session):
    return db.query(IncidentType).order_by(IncidentType.code).all()

def create_type(db: Session, data: IncidentTypeCreate):
    # Prüfen ob Code schon existiert
    if db.query(IncidentType).filter(IncidentType.code == data.code).first():
        return None
    
    obj = IncidentType(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_type(db: Session, code: str, data: IncidentTypeUpdate):
    obj = db.query(IncidentType).filter(IncidentType.code == code).first()
    if obj:
        if data.name is not None: 
            obj.name = data.name
        if data.description is not None: 
            obj.description = data.description
        if data.prompt_ref is not None: 
            obj.prompt_ref = data.prompt_ref
        
        db.commit()
        db.refresh(obj)
    return obj

def delete_type(db: Session, code: str):
    obj = db.query(IncidentType).filter(IncidentType.code == code).first()
    if obj:
        db.delete(obj)
        db.commit()
        return True
    return False