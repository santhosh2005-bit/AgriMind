"""Schemas for execution tracing, model observability, recovery tracking, and telemetry."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field
from backend.app.schemas.enums import ModelProvider, RecoveryAction, StepStatus


class ModelCallRecord(BaseModel):
    """Detailed record of an invocation to a foundation model."""
    call_id: str = Field(default_factory=lambda: str(uuid4()))
    step_id: str = Field(..., description="Associated plan step ID")
    model_id: str = Field(..., description="Target model identifier")
    provider: ModelProvider = Field(..., description="Provider invoked")
    prompt_tokens: Optional[int] = Field(None, ge=0)
    completion_tokens: Optional[int] = Field(None, ge=0)
    total_tokens: Optional[int] = Field(None, ge=0)
    estimated_cost_usd: Optional[float] = Field(None, ge=0)
    latency_ms: float = Field(..., ge=0)
    status: StepStatus = Field(default=StepStatus.COMPLETED)
    error_message: Optional[str] = None
    is_mock: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RecoveryEvent(BaseModel):
    """Log entry when a failure occurred and a recovery mechanism was triggered."""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    step_id: str = Field(..., description="Plan step that experienced the failure")
    trigger_reason: str = Field(..., description="E.g., 'timeout', 'rate_limit', 'schema_validation_failed'")
    action_taken: RecoveryAction = Field(...)
    from_target: str = Field(..., description="Failing model or tool name")
    to_target: Optional[str] = Field(None, description="Fallback model or strategy selected")
    success: bool = Field(..., description="Whether recovery successfully yielded output")
    details: str = Field(..., description="Contextual narrative of the recovery event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionTrace(BaseModel):
    """Comprehensive observability trace for a full workflow execution run."""
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str = Field(...)
    plan_id: Optional[str] = None
    model_calls: List[ModelCallRecord] = Field(default_factory=list)
    recovery_events: List[RecoveryEvent] = Field(default_factory=list)
    total_latency_ms: float = Field(default=0.0, ge=0)
    total_estimated_cost_usd: float = Field(default=0.0, ge=0)
    total_steps_executed: int = Field(default=0, ge=0)
    fallbacks_count: int = Field(default=0, ge=0)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
