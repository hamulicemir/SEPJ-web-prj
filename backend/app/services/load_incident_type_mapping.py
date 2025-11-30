# app/services/load_incident_type_mapping.py
import sqlalchemy as sa
from app.db import engine
import logging

def load_incident_type_mapping():
    """Lädt die Zuordnung von Vorfallnamen zu Codes aus der Datenbank."""
    query = sa.text("""
        SELECT code, name
        FROM incident_types
    """)

    with engine.connect() as conn:
        rows = conn.execute(query).mappings().fetchall()

    mapping = {}
    for r in rows:
        mapping[r["name"].strip().lower()] = r["code"].strip().lower()

    return mapping