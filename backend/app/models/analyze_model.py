# app/models/analyze_model.py
from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    text: str
