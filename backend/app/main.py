from fastapi import FastAPI, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .db import engine
from sqlalchemy import text
import sqlalchemy as sa
from dotenv import load_dotenv
import os, httpx, logging
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# Umgebungsvariablen laden
# -----------------------------------------------------------------------------
load_dotenv()

# -----------------------------------------------------------------------------
# Basis-Setup
# -----------------------------------------------------------------------------
app = FastAPI(title="SEPJ Backend API")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # wenn du willst: ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    url = f"{base}/api/tags"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            logger.info("OLLAMA_PING status=%s body=%s", resp.status_code, resp.text)
            resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        # Ollama antwortet, aber mit Fehlerstatus (z.B. 404, 500)
        logger.error(
            "Ollama HTTP-Fehler beim Ping: status=%s body=%s",
            e.response.status_code,
            e.response.text,
        )
        raise HTTPException(
            status_code=502,
            detail={
                "msg": "Ollama HTTP-Fehler beim Ping",
                "status": e.response.status_code,
                "body": e.response.text,
                "base_url": base,
            },
        )
    except httpx.RequestError as e:
        # Verbindungsproblem (DNS, Timeout, Connection refused, ...)
        logger.error("Ollama nicht erreichbar beim Ping: %r", e)
        raise HTTPException(
            status_code=502,
            detail={
                "msg": "Ollama nicht erreichbar",
                "base_url": base,
                "error": str(e),
            },
        )

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
    """Lädt alle Vorfallstypen aus der Datenbank und gibt strukturierte Infos zurück."""
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                sa.text("SELECT code, name, description FROM incident_types ORDER BY code")
            ).fetchall()
            types = [{"code": r[0], "name": r[1], "desc": r[2]} for r in rows]
            logger.info(f"{len(types)} Vorfallstypen aus DB geladen: {[t['code'] for t in types]}")
            return types
    except Exception as e:
        logger.warning(f"Vorfallstypen konnten nicht aus DB gelesen werden: {e}")
        # Fallback (nur Codes, falls DB-Fehler)
        return [
            {"code": c, "name": c.capitalize(), "desc": ""}
            for c in [
                "einbruch",
                "sachbeschaedigung",
                "koerperverletzung",
                "brandstiftung",
                "selbstverletzung",
                "diebstahl",
            ]
        ]

def build_prompt(text: str, types: list[dict]) -> str:
    """Erstellt den Prompt für Gemma mit Beschreibungstexten."""
    lines = []
    for t in types:
        lines.append(f"- {t['name']} ({t['code']}): {t['desc']}")
    joined = "\n".join(lines)

    return (
        "Analysiere den folgenden Text und erkenne, ob einer oder mehrere der folgenden Vorfallstypen vorkommen:\n"
        f"{joined}\n\n"
        "Antworte nur mit einer durch Komma getrennten Liste der erkannten Typen "
        "(z. B. 'brandstiftung, diebstahl') oder schreibe 'keiner', wenn nichts passt.\n\n"
        f"TEXT:\n{text}"
    )

# -----------------------------------------------------------------------------
# Kern-Endpoint
# -----------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    text: str

@app.post("/api/llm/analyze")
async def analyze_incident(payload: AnalyzeRequest):
    """
    Erwartete Quelle: JSON { "text": "..." }.
    Schickt den Inhalt an Gemma und loggt die Antwort.
    """
    text = payload.text

    if not text.strip():
        raise HTTPException(status_code=400, detail="Leerer Text übergeben.")

    # Vorfallstypen aus DB
    types = load_incident_types()
    prompt = build_prompt(text, types)

    base = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model = os.getenv("OLLAMA_MODEL", "gemma:2b")
    url = f"{base}/api/generate"

    ollama_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 64, "temperature": 0},
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            logger.info("Sende Anfrage an Ollama: url=%s model=%s", url, model)
            resp = await client.post(url, json=ollama_payload)
            logger.info(
                "OLLAMA_GENERATE status=%s body=%s",
                resp.status_code,
                resp.text[:1000],  # Body gekürzt loggen
            )
            resp.raise_for_status()
            data = resp.json()

    except httpx.HTTPStatusError as e:
        # Ollama hat geantwortet, aber mit Fehlerstatus (z.B. 404: Modell nicht gefunden)
        status = e.response.status_code
        body = e.response.text
        logger.error(
            "Ollama HTTP-Fehler bei /api/generate: status=%s body=%s",
            status,
            body,
        )
        raise HTTPException(
            status_code=502,
            detail={
                "msg": "Ollama HTTP-Fehler bei /api/generate",
                "status": status,
                "body": body,
                "base_url": base,
                "model": model,
            },
        )

    except httpx.RequestError as e:
        # Netzwerkproblem, z.B. Timeout, DNS, Connection refused
        logger.error("Ollama-Verbindungsfehler bei /api/generate: %r", e)
        raise HTTPException(
            status_code=502,
            detail={
                "msg": "Ollama-Verbindungsfehler bei /api/generate",
                "base_url": base,
                "model": model,
                "error": str(e),
            },
        )

    except Exception as e:
        # Unerwarteter Fehler im Backend (JSON-Parsing, KeyError, etc.)
        logger.exception("Unerwarteter Fehler in analyze_incident")
        raise HTTPException(
            status_code=500,
            detail="Unerwarteter Fehler im Backend bei der LLM-Analyse.",
        )

    # Ausgabe / Logging
    result = data.get("response", "").strip()

    logger.info("---- GEMMA RESPONSE BEGIN ----")
    logger.info(result)
    logger.info("---- GEMMA RESPONSE END ----")

    return {
        "status": "ok",
        "result": result,
        "model": model,
        "chars_in": len(text),
        "logged": True,
    }