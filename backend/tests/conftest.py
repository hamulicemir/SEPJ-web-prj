import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importiert App und DB-Logik
from app.db.session import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://sepj:sepj_secret@db:5432/sepj_db"
)

# Verbindung zur echten DB herstellen
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def setup_database():
    """
    Stellt sicher, dass die Tabellen existieren.
    Läuft nur 1x pro kompletten Test-Durchlauf.
    """
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture(scope="function")
def test_db(setup_database):
    """
    Erstellt für jeden einzelnen Test eine isolierte Transaktion.
    Am Ende wird alles rückgängig gemacht (Rollback).
    """
    # Verbindung öffnen & Transaktion starten
    connection = engine.connect()
    transaction = connection.begin()
    
    session = TestingSessionLocal(bind=connection)
    
    def override_get_db():
        try:
            yield session
        finally:
            pass 
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    # Alles rückgängig machen
    session.close()
    transaction.rollback()
    connection.close()
    
    app.dependency_overrides.clear()

@pytest.fixture(scope="module")
def client():
    """
    Der Test-Client für API-Anfragen.
    """
    with TestClient(app) as c:
        yield c