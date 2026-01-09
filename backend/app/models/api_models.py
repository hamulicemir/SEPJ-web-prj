from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime

class IncidentTypeBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    prompt_ref: Optional[str] = None

class IncidentTypeCreate(IncidentTypeBase):
    pass

class IncidentTypeOut(IncidentTypeBase):
    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    incident_type: str
    question_key: str
    label: str
    answer_type: str = "text"
    required: bool = False
    order_index: int = 0

class QuestionCreate(QuestionBase):
    pass

class QuestionOut(QuestionBase):
    id: int
    class Config:
        from_attributes = True

class PromptBase(BaseModel):
    name: str
    purpose: str
    content: str
    version_tag: Optional[str] = "v1"

class PromptCreate(PromptBase):
    pass

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

class LLMRunOut(BaseModel):
    id: UUID
    purpose: str
    model_name: str
    request_json: Optional[Any] = None
    response_json: Optional[Any] = None
    tokens_prompt: Optional[int]
    tokens_completion: Optional[int]
    latency_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class MetricRequest(BaseModel):
    text1: str
    text2: str

class MetricResponse(BaseModel):
    similarity_ratio: float
    details: Optional[str] = None