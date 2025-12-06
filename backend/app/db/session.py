from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

from app.models.db_models import Base


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL ist nicht gesetzt oder konnte nicht geladen werden")

engine = create_engine(
    DATABASE_URL,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


