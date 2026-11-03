"""Schemas for execution planning, step definition, and DAG tracking."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field
from backend.app.schemas.enums import TaskType, StepStatus, InputModality


class PlanStep(BaseModel):
    """An individual discrete step within the agentic execution plan."""
    step_id: str = Field(default_factory=lambda: str(uuid4()))
    step_number: int = Field(..., ge=1, description="Sequential ordering or display index")
    title: str = Field(..., min_length=2, description="Short human-readable summary of the step")
    description: str = Field(..., description="Actionable instruction or purpose of the step")
    task_type: TaskType = Field(..., description="Classification category for routing and execution")
    required_modalities: List[InputModality] = Field(default_factory=list, description="Modalities required")
    dependencies: List[str] = Field(default_factory=list, description="IDs of steps that must complete first")
    assigned_model_id: Optional[str] = Field(None, description="Model identifier chosen by router")
    assigned_tool_name: Optional[str] = Field(None, description="Tool name if this is a tool execution step")
    status: StepStatus = Field(default=StepStatus.PENDING, description="Current execution status")
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=2, ge=0)
    estimated_latency_ms: Optional[float] = Field(None, ge=0)
    estimated_cost_usd: Optional[float] = Field(None, ge=0)
    actual_latency_ms: Optional[float] = Field(None, ge=0)
    actual_cost_usd: Optional[float] = Field(None, ge=0)
    error_message: Optional[str] = Field(None, description="Recorded error message if failed")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExecutionPlan(BaseModel):
    """Structured plan orchestrating multiple model, retrieval, and tool steps."""
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str = Field(..., description="Associated request identifier")
    steps: List[PlanStep] = Field(..., min_length=1, description="List of plan steps")
    rationale: str = Field(..., description="Explicit explanation of why these steps were scheduled")
    execution_budget_seconds: int = Field(default=120, ge=5, le=600)
    estimated_total_cost_usd: Optional[float] = Field(default=0.0, ge=0)
    estimated_total_latency_ms: Optional[float] = Field(default=0.0, ge=0)
    is_validated: bool = Field(default=False, description="Whether plan passed pre-execution validation checks")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_step_by_id(self, step_id: str) -> Optional[PlanStep]:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_executable_steps(self) -> List[PlanStep]:
        """Return steps whose dependencies are completed and status is pending."""
        completed_ids = {s.step_id for s in self.steps if s.status == StepStatus.COMPLETED}
        return [
            s for s in self.steps
            if s.status == StepStatus.PENDING and all(dep in completed_ids for dep in s.dependencies)
        ]
