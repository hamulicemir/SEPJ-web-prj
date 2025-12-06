# app/services/incident_service.py
import sqlalchemy as sa
import logging
from app.db.session import engine

logger = logging.getLogger(__name__)

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
        logger.warning("Falling back to default incident types")
        fallback = [
            "einbruch", "sachbeschaedigung", "koerperverletzung",
            "brandstiftung", "selbstverletzung"
        ]
        return [{"code": c, "name": c.capitalize(), "desc": ""} for c in fallback]
