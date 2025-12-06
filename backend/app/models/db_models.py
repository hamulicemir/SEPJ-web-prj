import uuid
from sqlalchemy import (
    Column,
    Text,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class RawReport(Base):
    __tablename__ = "raw_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=True)
    body = Column(Text, nullable=False)
    language = Column(Text, nullable=True, default="de")
    source = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    incidents = relationship("Incident", back_populates="report")
    llm_runs = relationship("LLMRun", back_populates="report")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("raw_reports.id", ondelete="CASCADE"), nullable=False)
    incident_type = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="new")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    report = relationship("RawReport", back_populates="incidents")
    answers = relationship("StructuredAnswer", back_populates="incident")
    llm_runs = relationship("LLMRun", back_populates="incident")


class IncidentType(Base):
    __tablename__ = "incident_types"

    code = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    prompt_ref = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IncidentQuestion(Base):
    __tablename__ = "incident_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_type = Column(Text, ForeignKey("incident_types.code", ondelete="CASCADE"), nullable=False)
    question_key = Column(Text, nullable=False)
    label = Column(Text, nullable=False)
    answer_type = Column(Text, nullable=False)
    required = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)


class StructuredAnswer(Base):
    __tablename__ = "structured_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    question_key = Column(Text, nullable=False)
    value_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    incident = relationship("Incident", back_populates="answers")


class FinalReport(Base):
    __tablename__ = "final_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    body_md = Column(Text, nullable=False)
    model_name = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LLMRun(Base):
    __tablename__ = "llm_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purpose = Column(Text, nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey("raw_reports.id", ondelete="SET NULL"), nullable=True)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    model_name = Column(Text, nullable=False)
    request_json = Column(JSONB, nullable=False)
    response_json = Column(JSONB, nullable=True)
    tokens_prompt = Column(Integer, nullable=True)
    tokens_completion = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    report = relationship("RawReport", back_populates="llm_runs")
    incident = relationship("Incident", back_populates="llm_runs")


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    purpose = Column(Text, nullable=False)
    version_tag = Column(Text, nullable=True, default="v1")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
