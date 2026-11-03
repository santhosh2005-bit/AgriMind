"""SQLAlchemy ORM models for telemetry, execution runs, traces, and feedback."""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserSessionRecord(Base):
    """Multi-turn user sessions."""
    __tablename__ = "user_sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    user_metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship to execution runs
    runs = relationship("ExecutionRunRecord", back_populates="session", cascade="all, delete-orphan")


class ExecutionRunRecord(Base):
    """Primary telemetry log for each end-to-end user request run."""
    __tablename__ = "execution_runs"

    run_id = Column(String(64), primary_key=True, index=True)
    session_id = Column(String(64), ForeignKey("user_sessions.session_id"), nullable=True, index=True)
    request_id = Column(String(64), index=True)
    query_text = Column(Text, nullable=False)
    crop = Column(String(100), nullable=True)
    location_name = Column(String(100), nullable=True)
    status = Column(String(32), default="completed")  # "completed", "failed"
    verification_status = Column(String(32), default="passed")
    confidence_level = Column(String(32), default="medium")
    heuristic_score = Column(Float, default=0.5)
    total_latency_ms = Column(Float, default=0.0)
    total_cost_usd = Column(Float, default=0.0)
    total_tokens = Column(Integer, default=0)
    step_count = Column(Integer, default=0)
    final_answer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("UserSessionRecord", back_populates="runs")
    steps = relationship("PlanStepRecord", back_populates="run", cascade="all, delete-orphan")
    model_calls = relationship("ModelCallRecord", back_populates="run", cascade="all, delete-orphan")
    tool_invocations = relationship("ToolInvocationRecord", back_populates="run", cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceRecord", back_populates="run", cascade="all, delete-orphan")
    verification_checks = relationship("VerificationCheckRecord", back_populates="run", cascade="all, delete-orphan")
    recovery_events = relationship("RecoveryEventRecord", back_populates="run", cascade="all, delete-orphan")
    feedback = relationship("UserFeedbackRecord", back_populates="run", cascade="all, delete-orphan")


class PlanStepRecord(Base):
    """Detailed record of an executed step in the LangGraph DAG plan."""
    __tablename__ = "plan_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("execution_runs.run_id"), index=True, nullable=False)
    step_id = Column(String(64), index=True)
    step_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    task_type = Column(String(64), nullable=False)
    assigned_model_id = Column(String(128), nullable=True)
    status = Column(String(32), default="completed")
    latency_ms = Column(Float, default=0.0)
    cost_usd = Column(Float, default=0.0)
    dependencies_json = Column(Text, default="[]")
    error_message = Column(Text, nullable=True)

    run = relationship("ExecutionRunRecord", back_populates="steps")


class ModelCallRecord(Base):
    """Granular audit record of every individual model invocation."""
    __tablename__ = "model_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("execution_runs.run_id"), index=True, nullable=False)
    step_id = Column(String(64), index=True)
    model_id = Column(String(128), nullable=False)
    provider = Column(String(64), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    is_mock = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    run = relationship("ExecutionRunRecord", back_populates="model_calls")


class ToolInvocationRecord(Base):
    """Audit record of external API, retrieval, and tabular tool calls."""
    __tablename__ = "tool_invocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("execution_runs.run_id"), index=True, nullable=False)
    step_id = Column(String(64), index=True)
    tool_name = Column(String(128), nullable=False)
    status = Column(String(32), default="success")
    parameters_json = Column(Text, default="{}")
    latency_ms = Column(Float, default=0.0)
    is_mock = Column(Boolean, default=False)
    raw_output_snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    run = relationship("ExecutionRunRecord", back_populates="tool_invocations")


class EvidenceRecord(Base):
    """Indexed factual evidence items retrieved and cited during execution."""
    __tablename__ = "evidence_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("execution_runs.run_id"), index=True, nullable=False)
    source_type = Column(String(64), nullable=False)
    source_name = Column(String(255), nullable=False)
    location_reference = Column(String(255), nullable=True)
    content_snippet = Column(Text, nullable=False)
    relevance_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    run = relationship("ExecutionRunRecord", back_populates="evidence_items")


class VerificationCheckRecord(Base):
    """Audit record of individual checks conducted by the Verification Critic."""
    __tablename__ = "verification_checks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("execution_runs.run_id"), index=True, nullable=False)
    check_type = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    target_claim = Column(Text, nullable=True)
    details = Column(Text, nullable=False)
    deterministic_passed = Column(Boolean, nullable=True)

    run = relationship("ExecutionRunRecord", back_populates="verification_checks")


class RecoveryEventRecord(Base):
    """Telemetry log of automated self-correction, fallbacks, or escalations."""
    __tablename__ = "recovery_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("execution_runs.run_id"), index=True, nullable=False)
    step_id = Column(String(64))
    trigger_reason = Column(Text, nullable=False)
    action_taken = Column(String(64), nullable=False)
    from_target = Column(String(128))
    to_target = Column(String(128))
    success = Column(Boolean, default=True)
    details = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    run = relationship("ExecutionRunRecord", back_populates="recovery_events")


class UserFeedbackRecord(Base):
    """Post-execution human rating and feedback."""
    __tablename__ = "user_feedback"

    feedback_id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), ForeignKey("execution_runs.run_id"), index=True, nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5
    is_helpful = Column(Boolean, default=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    run = relationship("ExecutionRunRecord", back_populates="feedback")
