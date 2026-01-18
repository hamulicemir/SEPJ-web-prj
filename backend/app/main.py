from fastapi import FastAPI
from app.config import create_app
from app.routes.health import router as health_router
from app.routes.llm_ping import router as ping_router
from app.routes.analyze import router as analyze_router
from app.routes.reports import router as report_router
from app.routes.admin import router as admin_router
from app.routes.evaluation import router as evaluation_router

app: FastAPI = create_app()

app.include_router(health_router)
app.include_router(ping_router)
app.include_router(analyze_router)
app.include_router(admin_router)
app.include_router(report_router)
app.include_router(evaluation_router)