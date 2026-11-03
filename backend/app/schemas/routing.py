"""Schemas for model capabilities and transparent routing decisions."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field
from backend.app.schemas.enums import TaskType, ModelProvider, DeploymentType, InputModality


class ModelProfile(BaseModel):
    """Specification of an AI model registered in the system."""
    model_id: str = Field(..., description="Unique model identifier, e.g. gemini-1.5-flash")
    display_name: str = Field(..., description="Human-friendly model title")
    provider: ModelProvider = Field(..., description="Inference provider")
    deployment_type: DeploymentType = Field(..., description="Commercial cloud vs local open-weight")
    supported_modalities: List[InputModality] = Field(..., min_length=1)
    supported_task_types: List[TaskType] = Field(..., min_length=1)
    max_context_tokens: int = Field(default=8192, ge=512)
    supports_structured_output: bool = Field(default=False)
    supports_vision: bool = Field(default=False)
    supports_tool_calling: bool = Field(default=False)
    cost_per_1k_prompt_tokens_usd: float = Field(default=0.0, ge=0)
    cost_per_1k_completion_tokens_usd: float = Field(default=0.0, ge=0)
    typical_latency_ms: float = Field(default=500.0, ge=0)
    is_available: bool = Field(default=True)
    timeout_seconds: int = Field(default=30, ge=1)
    failure_count: int = Field(default=0, ge=0)
    total_calls: int = Field(default=0, ge=0)


class RoutingDecision(BaseModel):
    """Transparent record of why a specific model was assigned to a task."""
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    step_id: str = Field(..., description="Associated plan step ID")
    task_type: TaskType = Field(..., description="Task category being routed")
    selected_model_id: str = Field(..., description="Chosen model identifier")
    selected_provider: ModelProvider = Field(..., description="Provider of chosen model")
    rationale: str = Field(..., min_length=5, description="Clear technical explanation of routing choice")
    fallback_model_id: Optional[str] = Field(None, description="Pre-designated fallback model if primary fails")
    fallback_provider: Optional[ModelProvider] = None
    estimated_cost_usd: float = Field(default=0.0, ge=0)
    estimated_latency_ms: float = Field(default=0.0, ge=0)
    decision_factors: Dict[str, Any] = Field(
        default_factory=dict,
        description="Scoring breakdown (e.g. capability_match, cost_weight, latency_weight, availability)"
    )
    is_fallback: bool = Field(default=False, description="True if this decision is activating a fallback route")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
