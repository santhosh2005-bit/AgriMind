"""Shared execution state for AgriMind LangGraph agentic workflow."""

from typing import Dict, List, Optional, Any, Annotated
import time
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.app.schemas.enums import (
    InputModality,
    TaskType,
    StepStatus,
    VerificationStatus,
    ConfidenceLevel,
)
from backend.app.schemas.request import UserRequest
from backend.app.schemas.plan import ExecutionPlan, PlanStep
from backend.app.schemas.routing import RoutingDecision
from backend.app.schemas.tools import ToolResult, RetrievedEvidence
from backend.app.schemas.verification import VerificationResult
from backend.app.schemas.trace import RecoveryEvent, ExecutionTrace, ModelCallRecord
from backend.app.schemas.response import FinalResponse


class AgriMindState(BaseModel):
    """
    Shared workflow state passed through all LangGraph nodes.
    Maintains request context, DAG execution plan, intermediate results,
    retrieved evidence, model decisions, verification verdicts, and telemetry.
    """
    # 1. Input & Request Context
    request: UserRequest
    detected_modalities: List[InputModality] = Field(default_factory=list)
    request_understanding: Dict[str, Any] = Field(default_factory=dict)

    # 2. Planning & DAG Execution
    execution_plan: Optional[ExecutionPlan] = None
    current_step_index: int = 0
    step_statuses: Dict[str, StepStatus] = Field(default_factory=dict)
    intermediate_results: Dict[str, Any] = Field(default_factory=dict)

    # 3. Grounded Evidence & Tool Tracking
    retrieved_evidence: List[RetrievedEvidence] = Field(default_factory=list)
    model_decisions: Dict[str, RoutingDecision] = Field(default_factory=dict)
    tool_results: Dict[str, ToolResult] = Field(default_factory=dict)

    # 4. Verification, Critic & Recovery
    verification_result: Optional[VerificationResult] = None
    recovery_events: List[RecoveryEvent] = Field(default_factory=list)

    # 5. Output & Telemetry
    final_response: Optional[FinalResponse] = None
    trace: ExecutionTrace = Field(
        default_factory=lambda: ExecutionTrace(request_id="init")
    )
    execution_errors: List[str] = Field(default_factory=list)

    # 6. Execution Budgets & Safeguards
    started_at_timestamp: float = Field(default_factory=time.time)
    execution_budget_seconds: int = 120
    loop_iteration_count: int = 0
    max_loop_iterations: int = 20
    is_completed: bool = False

    def is_budget_exceeded(self) -> bool:
        """Check if execution elapsed time exceeds configured budget."""
        return (time.time() - self.started_at_timestamp) > self.execution_budget_seconds

    def has_pending_steps(self) -> bool:
        """Check if there are remaining pending steps in the execution plan."""
        if not self.execution_plan:
            return False
        return any(
            self.step_statuses.get(step.step_id, StepStatus.PENDING) == StepStatus.PENDING
            for step in self.execution_plan.steps
        )

    def get_next_step(self) -> Optional[PlanStep]:
        """Return the next executable step whose dependencies are completed."""
        if not self.execution_plan:
            return None
        completed_step_ids = {
            step_id for step_id, status in self.step_statuses.items()
            if status in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED)
        }
        for step in self.execution_plan.steps:
            if self.step_statuses.get(step.step_id, StepStatus.PENDING) == StepStatus.PENDING:
                if all(dep in completed_step_ids for dep in step.dependencies):
                    return step
        return None
