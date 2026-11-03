"""Adaptive execution engine handling routing, model invocation, and transparent fault recovery."""

import logging
import time
from typing import List, Optional, Tuple, Dict, Any, Type
from pydantic import BaseModel

from backend.app.schemas.enums import (
    InputModality,
    TaskType,
    ConfidenceLevel,
    StepStatus,
    RecoveryAction,
)
from backend.app.schemas.routing import RoutingDecision
from backend.app.schemas.trace import RecoveryEvent
from backend.app.models.base import ModelResponse, BaseModelAdapter
from backend.app.models.registry import ModelRegistry, default_registry
from backend.app.routing.router import ModelRouter, default_router

logger = logging.getLogger("agrimind.engine")


class RoutedExecutionEngine:
    """
    Executes a task through the ModelRouter with automatic fallback recovery:
    1. Routes the step to the highest-scoring compatible model.
    2. Attempts execution with bounded timeout.
    3. If primary model fails or times out, activates pre-designated fallback route.
    4. Produces transparent telemetry records for every decision and recovery event.
    """

    def __init__(self, router: Optional[ModelRouter] = None, registry: Optional[ModelRegistry] = None):
        self.registry = registry or default_registry
        self.router = router or default_router

    def execute_routed_step(
        self,
        step_id: str,
        task_type: TaskType,
        prompt: str,
        system_instruction: Optional[str] = None,
        images: Optional[List[bytes]] = None,
        response_schema: Optional[Type[BaseModel]] = None,
        required_modalities: Optional[List[InputModality]] = None,
        prior_confidence: Optional[ConfidenceLevel] = None,
        temperature: float = 0.2,
        max_retries: int = 2,
    ) -> Tuple[ModelResponse, RoutingDecision, Optional[RecoveryEvent]]:
        """
        Routes and executes the step.
        Returns: (ModelResponse, RoutingDecision, Optional[RecoveryEvent])
        """
        modalities = required_modalities or ([InputModality.IMAGE, InputModality.TEXT] if images else [InputModality.TEXT])

        # Step 1: Compute optimal routing decision
        decision = self.router.route_step(
            step_id=step_id,
            task_type=task_type,
            required_modalities=modalities,
            prior_confidence=prior_confidence,
            estimated_prompt_tokens=max(10, len(prompt.split()) * 2),
        )

        primary_adapter = self.registry.get_adapter(decision.selected_model_id)
        recovery_event: Optional[RecoveryEvent] = None

        # Step 2: Attempt primary execution with retry loop
        for attempt in range(max_retries + 1):
            try:
                response = primary_adapter.generate(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    images=images,
                    response_schema=response_schema,
                    temperature=temperature,
                )
                return response, decision, recovery_event

            except Exception as primary_error:
                logger.warning(
                    f"Attempt {attempt + 1} failed on primary model '{decision.selected_model_id}': {str(primary_error)}"
                )
                if attempt < max_retries:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue

                # Primary failed after all retries: trigger fallback if available
                if decision.fallback_model_id and self.registry.has_model(decision.fallback_model_id):
                    logger.warning(
                        f"Activating fallback route: Switching from '{decision.selected_model_id}' "
                        f"to '{decision.fallback_model_id}'"
                    )
                    fallback_adapter = self.registry.get_adapter(decision.fallback_model_id)

                    recovery_event = RecoveryEvent(
                        step_id=step_id,
                        trigger_reason=f"Primary model {decision.selected_model_id} failed after {max_retries + 1} attempts: {str(primary_error)}",
                        action_taken=RecoveryAction.FALLBACK_MODEL,
                        from_target=decision.selected_model_id,
                        to_target=decision.fallback_model_id,
                        success=False,
                        details="Transparent switchover to secondary compatible model in registry.",
                    )

                    try:
                        fallback_response = fallback_adapter.generate(
                            prompt=prompt,
                            system_instruction=system_instruction,
                            images=images if fallback_adapter.supports_modality(InputModality.IMAGE) else None,
                            response_schema=response_schema,
                            temperature=temperature,
                        )
                        recovery_event.success = True
                        fallback_response.raw_metadata["recovery_event_id"] = recovery_event.event_id
                        return fallback_response, decision, recovery_event

                    except Exception as fallback_error:
                        logger.error(
                            f"Fallback model '{decision.fallback_model_id}' also failed: {str(fallback_error)}"
                        )
                        recovery_event.success = False
                        recovery_event.details += f" | Fallback failed: {str(fallback_error)}"

                # If all configured live models failed, use mock fallback if enabled
                if settings.ENABLE_MOCK_FALLBACKS_FOR_TESTS:
                    from backend.app.models.adapters.mock_adapter import MockAdapter
                    mock = MockAdapter(model_id=f"mock-{decision.selected_model_id}")
                    res = mock.generate(prompt=prompt, images=images, response_schema=response_schema)
                    res.raw_metadata["fallback_reason"] = f"Primary and fallback live models failed ({str(primary_error)}); used mock"
                    return res, decision, recovery_event

                # No fallback configured: re-raise error
                raise primary_error


# Global shared execution engine
default_engine = RoutedExecutionEngine()
