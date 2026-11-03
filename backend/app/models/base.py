"""Abstract base class and common structures for all AI model adapters."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Type
from datetime import datetime, timezone
import time
from pydantic import BaseModel, Field

from backend.app.schemas.enums import InputModality, TaskType, ModelProvider, DeploymentType
from backend.app.schemas.routing import ModelProfile


class ModelResponse(BaseModel):
    """Standardized result returned by any model adapter."""
    content: str = Field(..., description="Generated textual response")
    structured_data: Optional[Dict[str, Any]] = Field(None, description="Parsed structured JSON if requested")
    model_id: str = Field(..., description="Model identifier that produced this output")
    provider: ModelProvider = Field(...)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0)
    latency_ms: float = Field(..., ge=0)
    is_mock: bool = Field(default=False, description="Flag indicating if a mock was used")
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LatencyStats:
    """Thread-safe latency and reliability tracker for a registered model."""

    def __init__(self, window_size: int = 50):
        self.window_size = window_size
        self.latencies: List[float] = []
        self.total_calls: int = 0
        self.failed_calls: int = 0
        self.total_tokens: int = 0
        self.total_cost_usd: float = 0.0

    def record_call(self, latency_ms: float, tokens: int = 0, cost_usd: float = 0.0, success: bool = True) -> None:
        self.total_calls += 1
        if success:
            self.latencies.append(latency_ms)
            if len(self.latencies) > self.window_size:
                self.latencies.pop(0)
            self.total_tokens += tokens
            self.total_cost_usd += cost_usd
        else:
            self.failed_calls += 1

    @property
    def average_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_l = sorted(self.latencies)
        idx = int(0.95 * len(sorted_l))
        return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def failure_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls


class BaseModelAdapter(ABC):
    """Abstract interface for all model providers (Gemini, Groq, Ollama, Mock)."""

    def __init__(self, profile: ModelProfile):
        self.profile = profile
        self.stats = LatencyStats()

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        images: Optional[List[bytes]] = None,
        response_schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        """Synchronous text / multimodal generation."""
        pass

    async def generate_async(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        images: Optional[List[bytes]] = None,
        response_schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        """Default async implementation delegating to generate."""
        return self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            images=images,
            response_schema=response_schema,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def supports_modality(self, modality: InputModality) -> bool:
        """Check if this model supports the specified input modality."""
        return modality in self.profile.supported_modalities

    def supports_task(self, task_type: TaskType) -> bool:
        """Check if this model is registered to handle this task type."""
        return task_type in self.profile.supported_task_types

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost in USD based on model rate card."""
        prompt_cost = (prompt_tokens / 1000.0) * self.profile.cost_per_1k_prompt_tokens_usd
        comp_cost = (completion_tokens / 1000.0) * self.profile.cost_per_1k_completion_tokens_usd
        return round(prompt_cost + comp_cost, 6)

    @abstractmethod
    def check_availability(self) -> bool:
        """Perform a quick health/ping check to determine if the provider is currently reachable."""
        pass

    def get_profile(self) -> ModelProfile:
        """Return profile with up-to-date availability and stats."""
        self.profile.is_available = self.check_availability()
        self.profile.typical_latency_ms = round(self.stats.average_latency_ms, 2) or self.profile.typical_latency_ms
        self.profile.failure_count = self.stats.failed_calls
        self.profile.total_calls = self.stats.total_calls
        return self.profile
