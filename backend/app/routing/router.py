"""Capability-aware model router for intelligent, cost-effective task distribution."""

import logging
from typing import List, Optional, Dict, Any
from uuid import uuid4

from backend.app.schemas.enums import InputModality, TaskType, ConfidenceLevel, ModelProvider
from backend.app.schemas.routing import RoutingDecision, ModelProfile
from backend.app.models.registry import ModelRegistry, default_registry
from backend.app.routing.scoring import is_hard_eligible, score_candidate

logger = logging.getLogger("agrimind.router")


class ModelRouter:
    """
    Evaluates execution plan steps and selects the optimal AI model or tool.
    Guarantees:
    1. Absolute capability matching (e.g. images only to vision models).
    2. Transparent, explainable scoring criteria.
    3. Low-confidence escalation to high-capacity reasoning models.
    4. Pre-designated fallbacks for high availability.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or default_registry

    def route_step(
        self,
        step_id: str,
        task_type: TaskType,
        required_modalities: Optional[List[InputModality]] = None,
        prior_confidence: Optional[ConfidenceLevel] = None,
        preferred_max_latency_ms: Optional[float] = None,
        estimated_prompt_tokens: int = 500,
        estimated_completion_tokens: int = 500,
    ) -> RoutingDecision:
        """
        Calculates the optimal model assignment for a workflow plan step.
        Logs and returns a transparent RoutingDecision record.
        """
        modalities = required_modalities or [InputModality.TEXT]

        # Check for tool-based tasks first
        if task_type == TaskType.WEATHER_RETRIEVAL:
            return RoutingDecision(
                step_id=step_id,
                task_type=task_type,
                selected_model_id="tool:weather_connector",
                selected_provider=ModelProvider.MOCK,
                rationale="Deterministic tool routing: Real-time weather data retrieved via Open-Meteo API rather than LLM invention.",
                estimated_cost_usd=0.0,
                estimated_latency_ms=250.0,
                decision_factors={"tool_type": "weather_api", "deterministic": True},
            )

        if task_type == TaskType.KNOWLEDGE_RETRIEVAL:
            return RoutingDecision(
                step_id=step_id,
                task_type=task_type,
                selected_model_id="tool:faiss_retriever",
                selected_provider=ModelProvider.MOCK,
                rationale="Deterministic tool routing: Agricultural guidelines retrieved from local FAISS vector index with page citations.",
                estimated_cost_usd=0.0,
                estimated_latency_ms=150.0,
                decision_factors={"tool_type": "vector_database", "deterministic": True},
            )

        if task_type == TaskType.WEB_SEARCH:
            return RoutingDecision(
                step_id=step_id,
                task_type=task_type,
                selected_model_id="tool:web_search",
                selected_provider=ModelProvider.MOCK,
                rationale="Deterministic tool routing: Live external web query retrieved with source citations and timeouts.",
                estimated_cost_usd=0.0,
                estimated_latency_ms=450.0,
                decision_factors={"tool_type": "web_search", "deterministic": True},
            )

        all_profiles = self.registry.list_profiles()
        eligible_candidates: List[tuple[ModelProfile, Dict[str, Any]]] = []
        rejections: Dict[str, str] = {}

        for profile in all_profiles:
            eligible, reason = is_hard_eligible(profile, task_type, modalities)
            if eligible:
                scored = score_candidate(
                    profile=profile,
                    task_type=task_type,
                    required_modalities=modalities,
                    prior_confidence=prior_confidence,
                    preferred_max_latency_ms=preferred_max_latency_ms,
                )
                eligible_candidates.append((profile, scored))
            else:
                rejections[profile.model_id] = reason or "Unknown incompatibility"

        if not eligible_candidates:
            # Fallback to general mock adapter if no registered models match
            logger.warning(
                f"No eligible models found for step '{step_id}' ({task_type.value}, {modalities}). "
                f"Rejections: {rejections}"
            )
            return RoutingDecision(
                step_id=step_id,
                task_type=task_type,
                selected_model_id="mock-agri-model",
                selected_provider=ModelProvider.MOCK,
                rationale=f"Fallback assignment: No models matched hard constraints ({rejections}); assigned mock engine.",
                estimated_cost_usd=0.0,
                estimated_latency_ms=100.0,
                decision_factors={"rejections": rejections, "fallback": True},
                is_fallback=True,
            )

        # Sort eligible candidates by composite score in descending order
        eligible_candidates.sort(key=lambda item: item[1]["composite_score"], reverse=True)

        winner_profile, winner_score = eligible_candidates[0]

        # Determine pre-designated fallback
        fallback_profile = None
        if len(eligible_candidates) > 1:
            fallback_profile = eligible_candidates[1][0]
        else:
            fallback_adapter = self.registry.get_fallback_for(winner_profile.model_id)
            if fallback_adapter:
                fallback_profile = fallback_adapter.profile

        # Calculate estimated cost for winning model
        winner_adapter = self.registry.get_adapter(winner_profile.model_id)
        estimated_cost = winner_adapter.estimate_cost(
            prompt_tokens=estimated_prompt_tokens,
            completion_tokens=estimated_completion_tokens,
        )

        # Construct clear technical rationale
        rationale_parts = [
            f"Selected {winner_profile.display_name} (Composite Score: {winner_score['composite_score']}).",
        ]
        if InputModality.IMAGE in modalities:
            rationale_parts.append("Step requires visual foliar inspection; model verified for native vision understanding.")
        if task_type in [TaskType.PLANNING, TaskType.AGRICULTURAL_REASONING]:
            rationale_parts.append(f"Task '{task_type.value}' requires high-capacity reasoning; context limit is {winner_profile.max_context_tokens} tokens.")
        if prior_confidence in [ConfidenceLevel.LOW, ConfidenceLevel.UNCERTAIN]:
            rationale_parts.append("Escalated model tier due to low confidence rating from prior step.")
        if winner_profile.cost_per_1k_prompt_tokens_usd == 0.0:
            rationale_parts.append("Utilizes local zero-cost inference.")

        rationale = " ".join(rationale_parts)

        decision = RoutingDecision(
            step_id=step_id,
            task_type=task_type,
            selected_model_id=winner_profile.model_id,
            selected_provider=winner_profile.provider,
            rationale=rationale,
            fallback_model_id=fallback_profile.model_id if fallback_profile else None,
            fallback_provider=fallback_profile.provider if fallback_profile else None,
            estimated_cost_usd=estimated_cost,
            estimated_latency_ms=winner_profile.typical_latency_ms,
            decision_factors={
                "scoring_breakdown": winner_score["breakdown"],
                "candidate_scores": {c[0].model_id: c[1]["composite_score"] for c in eligible_candidates},
                "excluded_candidates": rejections,
            },
        )

        logger.info(
            f"Routing decision for step '{step_id}' ({task_type.value}): "
            f"-> {decision.selected_model_id} (Fallback: {decision.fallback_model_id}) | Reason: {rationale}"
        )

        return decision


# Global shared router instance
default_router = ModelRouter()
