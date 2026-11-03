"""API endpoints for Model Router inspection and simulation."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.schemas.enums import InputModality, TaskType, ConfidenceLevel
from backend.app.schemas.routing import RoutingDecision
from backend.app.routing.router import default_router

router = APIRouter(prefix="/v1/routing", tags=["Model Router"])


class RoutingSimulateRequest(BaseModel):
    step_id: str = Field(default="sim-step-001")
    task_type: TaskType = Field(default=TaskType.VISION_ANALYSIS)
    required_modalities: List[InputModality] = Field(default=[InputModality.IMAGE, InputModality.TEXT])
    prior_confidence: Optional[ConfidenceLevel] = Field(default=None)
    preferred_max_latency_ms: Optional[float] = Field(default=None)


@router.post("/decide", response_model=RoutingDecision)
def simulate_routing_decision(req: RoutingSimulateRequest):
    """
    Simulate a routing decision for given task requirements.
    Returns complete candidate scores, chosen model, fallback model, and technical rationale.
    """
    decision = default_router.route_step(
        step_id=req.step_id,
        task_type=req.task_type,
        required_modalities=req.required_modalities,
        prior_confidence=req.prior_confidence,
        preferred_max_latency_ms=req.preferred_max_latency_ms,
    )
    return decision
