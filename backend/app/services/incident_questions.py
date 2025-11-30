# app/services/incident_questions.py
import sqlalchemy as sa
from app.db import engine
import logging

def load_incident_questions():
    logger = logging.getLogger(__name__)
    try:
        with engine.connect() as conn:
            rows = conn.execute(sa.text(
                "SELECT incident_type, questions_key, label, answer_type, order_index FROM incident_questions ORDER BY incident_type, order_index"
            )).fetchall()

        return [
            {
                "incident_type": r["incident_type"],
                "questions_key": r["questions_key"],
                "label": r["label"],
                "answer_type": r["answer_type"],
                "order_index": r["order_index"],
            }
            for r in rows
        ]

    except Exception as e:
        logger.warning("Fehler beim Laden der Incidient Questions %r", e)
        return []
        

def load_incident_questions_for_types(types: list[str]):
    if not types:
        return []

    query = sa.text("""
        SELECT incident_type, question_key, label, answer_type, order_index
        FROM incident_questions
        WHERE incident_type = ANY(:types)
        ORDER BY incident_type, order_index
    """)

    with engine.connect() as conn:
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