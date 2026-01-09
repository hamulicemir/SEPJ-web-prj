import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importiere deine App und DB-Logik
from app.db.session import Base, get_db
from app.main import app

# Wir nutzen die URL aus der Umgebung oder Fallback auf Docker-Standard
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
    # 1. Verbindung öffnen & Transaktion starten
    connection = engine.connect()
    transaction = connection.begin()
    
    # 2. Session an diese Verbindung binden
    session = TestingSessionLocal(bind=connection)
    
    # 3. Dependency Override: Zwingt die App, DIESE Session zu nutzen
    # Das ist der entscheidende Schritt, damit der API-Call nicht in die echte DB schreibt!
    def override_get_db():
        try:
            yield session
        finally:
            pass 
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    # 4. Aufräumen: Alles rückgängig machen
    session.close()
    transaction.rollback()
    connection.close()
    
    # Override entfernen, damit andere Tests nicht beeinflusst werden
    app.dependency_overrides.clear()

@pytest.fixture(scope="module")
def client():
    """
    Der Test-Client für API-Anfragen.
    """
    with TestClient(app) as c:
        yield c