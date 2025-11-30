# app/models/analyze_model.py
from pydantic import BaseModel

class IncidentQuestions(BaseModel):
    incident: str