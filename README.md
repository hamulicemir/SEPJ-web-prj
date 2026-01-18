# SEPJ – Projekt Setup (Docker Compose)

Dieses Repository enthält ein Full-Stack-Projekt mit:
- **PostgreSQL 16** (Datenbank)
- **Backend** (FastAPI/Uvicorn, Dockerfile im `./backend`)
- **Frontend** (Node 20, Dev-Server auf Port 5173)
- **Ollama** (LLM Runtime, z. B. `qwen:2.5:7b`)
- **Tests** (Pytest im Backend-Container)

---

## Voraussetzungen

- Docker + Docker Compose (Compose v2)
- Optional (für direkten Host-Aufruf von Ollama): `ollama` CLI lokal installiert  
  *Hinweis:* Für das Projekt ist Ollama bereits als Container vorhanden; das Modell kann auch im Container gepullt werden.

---

## Projektstruktur (überblick)

- `backend/` – Backend Code + Dockerfile
- `frontend/` – Frontend Code
- `db/sepj_init.sql` – SQL-Initialisierung für die Datenbank (Schema/Seed)
- `.env` – Umgebungsvariablen (lokal, nicht committen)

---

## Konfiguration (.env)

Lege im Projektroot eine Datei `.env` an (oder übernimm die folgende Vorlage):

```env
POSTGRES_USER=sepj
POSTGRES_PASSWORD=sepj_pw
POSTGRES_DB=sepj
POSTGRES_PORT=5432

API_PORT=8000
DB_HOST=db
DB_PORT=5432
DB_NAME=sepj
DB_USER=sepj
DB_PASSWORD=sepj_pw

DATABASE_URL=postgresql+psycopg://sepj:sepj_pw@db:5432/sepj

OLLAMA_PORT=11434
OLLAMA_MODEL=qwen:2.5:7b
```

Wichtig:
- `DB_HOST=db` verweist auf den Compose-Service `db`.
- `DATABASE_URL` ist die Connection-URL, die das Backend verwendet.

---

## Services & Ports

Nach dem Start sind die Services typischerweise erreichbar unter:

- **Frontend:** http://localhost:5173  
- **Backend (API):** http://localhost:8000  
- **PostgreSQL:** localhost:5432 (oder `${POSTGRES_PORT}`)  
- **Ollama:** http://localhost:11434 (oder `${OLLAMA_PORT}`)

---

## Start (Build + Run)

Im Projektroot:

```bash
docker compose up --build
```

Damit werden alle Services gebaut/gestartet.  
Die Datenbank wird dabei **als Container gestartet**, aber die **Initialisierung via SQL** erfolgt anschließend manuell (siehe nächster Abschnitt).

---

## Datenbank initialisieren

Voraussetzung: Der DB-Container läuft und ist „healthy“.

### 1) SQL-Init-Datei in den DB-Container kopieren

```bash
docker compose cp db/sepj_init.sql db:/sepj_init.sql
```

### 2) SQL im Container ausführen

```bash
docker compose exec db psql -U sepj -d sepj -f /sepj_init.sql
```

Hinweis:
- User/DB entsprechen den `.env` Werten (`POSTGRES_USER`, `POSTGRES_DB`).
- Wenn du andere Werte nutzt, passe `-U` und `-d` entsprechend an.

---

## Ollama Modell installieren (qwen:2.5:7b)

### Option A (empfohlen): Pull im Ollama-Container

```bash
docker compose exec ollama ollama pull qwen:2.5:7b
```

Hinweis:
- Das Backend verwendet im Compose standardmäßig:
  - `OLLAMA_BASE_URL=http://ollama:11434`
- Das Modell wird im Volume `ollama` persistent gespeichert.

---

## Tests ausführen

Die Tests sind als eigener Service definiert. Du kannst sie jederzeit laufen lassen mit:

```bash
docker compose run --rm tests
```

oder (falls der `tests` Service bereits existiert):

```bash
docker compose up --build tests
```

---

## Stoppen & Aufräumen

### Services stoppen
```bash
docker compose down
```

### Stoppen inkl. Volumes (löscht DB-Daten & Ollama Modelle)
```bash
docker compose down -v
```

---

## Troubleshooting

### DB ist nicht erreichbar / Backend startet nicht
- Backend hängt an `depends_on` mit Healthcheck der DB. Prüfe den DB-Status:
  ```bash
  docker compose ps
  ```
- Logs anschauen:
  ```bash
  docker compose logs -f db
  docker compose logs -f backend
  ```

### Datenbank neu initialisieren
Wenn du die DB komplett neu aufsetzen willst:
```bash
docker compose down -v
docker compose up --build
docker compose cp db/sepj_init.sql db:/sepj_init.sql
docker compose exec db psql -U sepj -d sepj -f /sepj_init.sql
```

### Ollama Modell fehlt
- Prüfe, ob das Modell im Ollama-Container vorhanden ist:
  ```bash
  docker compose exec ollama ollama list
  ```
- Modell nachziehen:
  ```bash
  docker compose exec ollama ollama pull qwen:2.5:7b
  ```

---

## Quickstart (alles in Reihenfolge)

```bash
# 1) Start
docker compose up --build -d

# 2) DB initialisieren
docker compose cp db/sepj_init.sql db:/sepj_init.sql
docker compose exec db psql -U sepj -d sepj -f /sepj_init.sql

# 3) Ollama Modell installieren
docker compose exec ollama ollama pull qwen:2.5:7b

# 4) (optional) Tests
docker compose run --rm tests
```
