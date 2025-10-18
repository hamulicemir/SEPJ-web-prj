from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from .db import engine
import sqlalchemy as sa
import os, httpx, logging

# -----------------------------------------------------------------------------
# Basis-Setup
# -----------------------------------------------------------------------------
app = FastAPI(title="SEPJ Backend API")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Healthcheck
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(sa.text("SELECT 1"))
    return {"status": "ok"}

# -----------------------------------------------------------------------------
# LLM-Ping (Verbindungscheck zu Ollama)
# -----------------------------------------------------------------------------
@app.get("/api/llm/ping")
async def llm_ping():
    base = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{base}/api/tags")
        r.raise_for_status()
    return {"ollama": "ok"}

# -----------------------------------------------------------------------------
# Hilfsfunktionen
# -----------------------------------------------------------------------------
DEFAULT_TYPES = [
    "einbruch",
    "sachbeschaedigung",
    "koerperverletzung",
    "brandstiftung",
    "diebstahl",
    "drogen",
    "gefängnisordnung_verstoss",
    "bedrohung"
]

def load_incident_types():
    """Lädt Vorfallstypen aus DB oder nutzt Fallback."""
    try:
        with engine.connect() as conn:
            rows = conn.execute(sa.text("SELECT code FROM incident_types")).fetchall()
            types = [r[0] for r in rows]
            return types if types else DEFAULT_TYPES
    except Exception as e:
        logger.warning(f"Vorfallstypen konnten nicht aus DB gelesen werden: {e}")
        return DEFAULT_TYPES

def build_prompt(text: str, types: list[str]) -> str:
    """Erstellt den eigentlichen Prompt für Gemma."""
    return (
        "Analysiere den folgenden Text und erkenne, ob einer oder mehrere "
        f"dieser Vorfallstypen vorkommen: {', '.join(types)}.\n"
        "Antworte nur mit einer durch Komma getrennten Liste der erkannten Typen, "
        "oder schreibe 'keiner', wenn nichts passt.\n\n"
        f"TEXT:\n{text}"
    )

async def fetch_text_from_url(url: str) -> str:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text

# -----------------------------------------------------------------------------
# Kern-Endpoint
# -----------------------------------------------------------------------------
@app.post("/api/llm/analyze")
async def analyze_incident(
    file: UploadFile | None = File(None),
    url: str | None = Form(None),
    text: str | None = Form(None),
):
    """
    Erwartet EINE Quelle: file ODER url ODER text.
    Schickt den Inhalt an Gemma und loggt die Antwort.
    """
    sources = [file is not None, url is not None, text is not None]
    if sum(sources) != 1:
        raise HTTPException(status_code=400, detail="Genau eine Quelle angeben (file, url oder text).")

    # -------------------------------
    # 1. Textinhalt beschaffen
    # -------------------------------
    if file is not None:
        if not file.filename.lower().endswith(".txt"):
            raise HTTPException(status_code=400, detail="Nur .txt-Dateien werden akzeptiert.")
        raw = await file.read()
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            content = raw.decode("latin-1")
    elif url is not None:
        content = await fetch_text_from_url(url)
    else:
        content = text or ""

    if not content.strip():
        raise HTTPException(status_code=400, detail="Leerer Text übergeben.")

    # -------------------------------
    # 2. Vorfallstypen & Prompt
    # -------------------------------
    types = load_incident_types()
    prompt = build_prompt(content, types)

    # -------------------------------
    # 3. Anfrage an Ollama / Gemma 2
    # -------------------------------
    base = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model = os.getenv("OLLAMA_MODEL", "gemma:2b")

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 64, "temperature": 0},
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{base}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Ollama-Fehler: {e}")

    # -------------------------------
    # 4. Ausgabe / Logging
    # -------------------------------
    result = data.get("response", "").strip()

    logger.info("---- GEMMA 2 RESPONSE BEGIN ----")
    logger.info(result)
    logger.info("---- GEMMA 2 RESPONSE END ----")

    # -------------------------------
    # 5. Rückgabe an Frontend (vorerst minimal)
    # -------------------------------
    return {
        "status": "ok",
        "model": model,
        "chars_in": len(content),
        "logged": True,  # Hinweis: echte Ausgabe steht nur im Log
    }


