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


def load_prompts(version: str = "v1") -> dict[str, str]:
    """Lädt base_prompt, classify_rules_prompt und info_prompt als Dict."""
    names = ["base_prompt", "classify_rules_prompt", "info_prompt"]
    result = {}

    query = text("""
        SELECT name, content
        FROM prompts
        WHERE name = ANY(:names) AND version_tag = :version
    """)

    with engine.connect() as conn:
        rows = conn.execute(
            query,
            {"names": names, "version": version}
        ).fetchall()

    if not rows:
        raise RuntimeError("Keine Prompts in der Datenbank gefunden!")

    for name, content in rows:
        result[name] = content

    # Sicherstellen, dass alle existieren
    for n in names:
        if n not in result:
            raise ValueError(f"Prompt '{n}' fehlt in der Datenbank!")

    return result


def load_incident_types():
    """Lädt alle Vorfallstypen aus der Datenbank und gibt strukturierte Infos zurück."""
    try:
        with engine.connect() as conn:
            rows = conn.execute(sa.text(
                "SELECT code, name, description FROM incident_types ORDER BY code"
            )).fetchall()

            types = [
                {"code": r[0], "name": r[1], "desc": r[2] or ""}
                for r in rows
            ]

            logger.info(f"{len(types)} Vorfallstypen aus DB geladen: {[t['code'] for t in types]}")
            return types

    except Exception as e:
        logger.warning(f"Vorfallstypen konnten nicht aus DB gelesen werden: {e}")

        # Minimaler Fallback
        fallback_codes = [
            "einbruch", "sachbeschaedigung", "koerperverletzung",
            "brandstiftung", "selbstverletzung", "diebstahl",
            "bedrohung", "noetigung", "belästigung", "alkohol_drogen"
        ]
        return [{"code": c, "name": c.capitalize(), "desc": ""} for c in fallback_codes]


"""
Wichtig:
Du sollst konservativ und streng klassifizieren nur wenn eine Handlung eindeutig beschrieben ist, ordnest du sie zu.
Wenn Unsicherheit besteht, wählst du keine oder weniger Kategorien.
"""

def build_prompt(text: str, types: list[dict], prompts: dict[str, str]) -> str:
    """
    prompts dict muss enthalten:
        - base_prompt
        - classify_rules_prompt
        - info_prompt
    """

    # Kategorienliste bauen
    type_lines = []
    for t in types:
        desc = (t["desc"] or "").strip()
        name = (t["name"] or "").strip()
        type_lines.append(f"- {name}: {desc}")

    categories_str = "\n".join(type_lines)

    # Prompt-Bausteine einsetzen
    base = prompts.get("base_prompt", "").strip()
    classify = prompts.get("classify_rules_prompt", "").strip()
    info = prompts.get("info_prompt", "").strip()

    # Vollständigen LLM-Prompt bauen
    return f"""
{base}

Vorfallstypen:
{categories_str}

{classify}

{info}
{text.strip()}
"""


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

     # 1) Vorfallstypen laden
    types = load_incident_types()

    # 2) Prompts aus Datenbank laden
    prompts = load_prompts()

    # 3) Finalen LLM-Prompt bauen
    prompt = build_prompt(text, types, prompts)

    logger.info("Generierter Prompt für LLM:\n%s", prompt)

    base = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model = os.getenv("OLLAMA_MODEL", "gemma:2b")
    #model = "qwen2.5:3b"
    url = f"{base}/api/generate"

    ollama_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            #"temperature": 0,
            #"top_k": 1,
            #"top_p": 1,
            #"repeat_penalty": 1.1,
            "num_predict": -1
            }
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