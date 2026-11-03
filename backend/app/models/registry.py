"""Central model registry managing model profiles, adapters, and availability status."""

from typing import Dict, List, Optional
import logging

from backend.app.schemas.enums import InputModality, TaskType, ModelProvider, DeploymentType
from backend.app.schemas.routing import ModelProfile
from backend.app.models.base import BaseModelAdapter
from backend.app.models.adapters.gemini_adapter import GeminiAdapter
from backend.app.models.adapters.groq_adapter import GroqAdapter
from backend.app.models.adapters.ollama_adapter import OllamaAdapter
from backend.app.models.adapters.mock_adapter import MockAdapter
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Central registry for multi-model orchestrations.
    Maintains active adapters, verifies capability classifications,
    and isolates provider details from higher-level routing.
    """

    def __init__(self):
        self._adapters: Dict[str, BaseModelAdapter] = {}

    def register(self, adapter: BaseModelAdapter) -> None:
        """Register an adapter instance keyed by its model_id."""
        self._adapters[adapter.profile.model_id] = adapter
        logger.info(
            f"Registered model '{adapter.profile.model_id}' "
            f"({adapter.profile.provider.value}, {adapter.profile.deployment_type.value})"
        )

    def get_adapter(self, model_id: str) -> BaseModelAdapter:
        """Retrieve an adapter by model_id; raises KeyError if not found."""
        if model_id not in self._adapters:
            raise KeyError(
                f"Model '{model_id}' is not registered. Available models: {list(self._adapters.keys())}"
            )
        return self._adapters[model_id]

    def has_model(self, model_id: str) -> bool:
        return model_id in self._adapters

    def list_profiles(self) -> List[ModelProfile]:
        """Return updated profiles for all registered models."""
        return [adapter.get_profile() for adapter in self._adapters.values()]

    def find_compatible_models(
        self,
        task_type: Optional[TaskType] = None,
        required_modalities: Optional[List[InputModality]] = None,
        provider: Optional[ModelProvider] = None,
        deployment_type: Optional[DeploymentType] = None,
        only_available: bool = False,
    ) -> List[BaseModelAdapter]:
        """
        Find models strictly matching all capability constraints.
        Distinguishes capabilities from assumptions:
        - If IMAGE is in required_modalities, rejects models where supports_vision=False.
        - If task_type is provided, ensures model's profile includes task_type.
        """
        matches: List[BaseModelAdapter] = []

        for adapter in self._adapters.values():
            profile = adapter.profile

            # Check modality requirements
            if required_modalities:
                if not all(adapter.supports_modality(m) for m in required_modalities):
                    continue
                if InputModality.IMAGE in required_modalities and not profile.supports_vision:
                    continue

            # Check task capability
            if task_type and not adapter.supports_task(task_type):
                continue

            # Filter by provider or deployment tier
            if provider and profile.provider != provider:
                continue
            if deployment_type and profile.deployment_type != deployment_type:
                continue

            # Check live availability
            if only_available and not adapter.check_availability():
                continue

            matches.append(adapter)

        return matches

    def get_fallback_for(self, model_id: str) -> Optional[BaseModelAdapter]:
        """
        Find a compatible alternative model if the primary model fails or times out.
        Prioritizes other registered models that share task capabilities.
        """
        primary = self.get_adapter(model_id)
        candidates = self.find_compatible_models(
            required_modalities=primary.profile.supported_modalities
        )
        for cand in candidates:
            if cand.profile.model_id != model_id:
                return cand

        # Fallback to general mock adapter if enabled
        if settings.ENABLE_MOCK_FALLBACKS_FOR_TESTS and "mock-agri-model" in self._adapters:
            return self._adapters["mock-agri-model"]

        return None


def create_default_registry() -> ModelRegistry:
    """Initialize registry with the 3 required categories plus the mock adapter."""
    registry = ModelRegistry()

    # Category A: Commercial Model 1 (Google Gemini - Multimodal / Vision)
    gemini = GeminiAdapter()
    registry.register(gemini)

    # Category B: Commercial Model 2 (Groq Cloud - Fast Structured Reasoning)
    groq = GroqAdapter()
    registry.register(groq)

    # Category C: Open-Weight Local Model (Ollama Llama 3.2 3B - Edge / Local)
    ollama = OllamaAdapter()
    registry.register(ollama)

    # Local Mock Adapter for deterministic offline tests and non-cloud execution
    mock = MockAdapter(model_id="mock-agri-model", display_name="Mock Agronomy Engine")
    registry.register(mock)

    return registry


# Global shared registry instance
default_registry = create_default_registry()
