# app/routes/health.py
from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import engine

router = APIRouter()

@router.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
