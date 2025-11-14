from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# .env laden
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL ist nicht gesetzt oder konnte nicht geladen werden")

# SQLAlchemy Engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
