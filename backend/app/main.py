# app/main.py
from fastapi import FastAPI
from app.config import create_app
from app.routes.health import router as health_router
from app.routes.llm_ping import router as ping_router
from app.routes.analyze import router as analyze_router

app: FastAPI = create_app()

# Routen registrieren
app.include_router(health_router)
app.include_router(ping_router)
app.include_router(analyze_router)
