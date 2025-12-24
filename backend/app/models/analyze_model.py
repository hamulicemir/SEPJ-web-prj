from pydantic import BaseModel
from typing import Optional, List, Any  # <--- Diese Zeile fehlte oder war unvollständig
from uuid import UUID
from datetime import datetime

# --- Bestehendes Request Model ---
class AnalyzeRequest(BaseModel):
    text: str
    title: Optional[str] = None

# --- NEU: Admin Schemas (Prompts, Types, Questions, Logs) ---

# Prompts
class PromptBase(BaseModel):
    name: str
    purpose: str
    content: str
    version_tag: Optional[str] = "v1"

class PromptUpdate(BaseModel):
    name: Optional[str] = None
    purpose: Optional[str] = None
    content: Optional[str] = None
    version_tag: Optional[str] = None

class PromptOut(PromptBase):
    id: UUID
    created_at: datetime
    class Config: 
        from_attributes = True

# Incident Types
class IncidentTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    prompt_ref: Optional[str] = None

class IncidentTypeCreate(IncidentTypeBase):
    code: str

class IncidentTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prompt_ref: Optional[str] = None

class IncidentTypeOut(IncidentTypeBase):
    code: str
    created_at: datetime
    class Config: 
        from_attributes = True

# Questions
class QuestionBase(BaseModel):
    incident_type: str
    question_key: str
    label: str
    answer_type: str = "text"
    required: bool = True
    order_index: int = 0

class QuestionUpdate(BaseModel):
    label: Optional[str] = None
    question_key: Optional[str] = None
    answer_type: Optional[str] = None
    required: Optional[bool] = None
    order_index: Optional[int] = None

class QuestionOut(QuestionBase):
    id: UUID
    class Config: 
        from_attributes = True

# Logs
class LLMRunOut(BaseModel):
    id: UUID
    purpose: str
    model_name: str
    tokens_prompt: Optional[int]
    tokens_completion: Optional[int]
    latency_ms: Optional[int]
    created_at: datetime
    class Config: 
        from_attributes = True

# Metrics
class MetricRequest(BaseModel):
    text1: str
    text2: str