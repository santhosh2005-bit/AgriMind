"""Scoring functions and transparent heuristics for the AgriMind Model Router."""

from typing import Dict, Any, List, Optional
from backend.app.schemas.enums import InputModality, TaskType, ConfidenceLevel
from backend.app.schemas.routing import ModelProfile


# Routing weights configuration (Capability-first to ensure high-grade models handle complex tasks)
WEIGHT_CAPABILITY = 0.45
WEIGHT_AVAILABILITY = 0.25
WEIGHT_COST = 0.15
WEIGHT_LATENCY = 0.15


def is_hard_eligible(
    profile: ModelProfile,
    task_type: TaskType,
    required_modalities: List[InputModality],
) -> tuple[bool, Optional[str]]:
    """
    Evaluates absolute hard constraints.
    Returns (eligible: bool, rejection_reason: Optional[str]).
    """
    # 1. Modality requirement
    for mod in required_modalities:
        if mod not in profile.supported_modalities:
            return False, f"Model lacks support for required modality '{mod.value}'"
        if mod == InputModality.IMAGE and not profile.supports_vision:
            return False, "Model is text-only and lacks vision comprehension capability"

    # 2. Task capability
    if task_type not in profile.supported_task_types:
        return False, f"Model is not registered for task type '{task_type.value}'"

    return True, None


def score_candidate(
    profile: ModelProfile,
    task_type: TaskType,
    required_modalities: List[InputModality],
    prior_confidence: Optional[ConfidenceLevel] = None,
    preferred_max_latency_ms: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Computes a transparent, multidimensional score for an eligible model.
    Higher score indicates better suitability.
    """
    # 1. Capability Match Score (0.0 to 1.0)
    # Simple tasks (classification, validation) can be handled by smaller models.
    # Complex tasks (planning, reasoning, verification) strictly benefit from larger frontier models.
    if task_type in [
        TaskType.PLANNING,
        TaskType.AGRICULTURAL_REASONING,
        TaskType.VERIFICATION,
        TaskType.GENERAL_REASONING,
        TaskType.CODE_ANALYSIS,
        TaskType.CALCULATION,
    ]:
        if profile.max_context_tokens >= 32000 and profile.supports_structured_output:
            cap_score = 1.0
        else:
            # Moderate penalty for small-context models on complex reasoning/code/math
            cap_score = 0.40
    elif task_type in [
        TaskType.INPUT_VALIDATION,
        TaskType.REQUEST_UNDERSTANDING,
        TaskType.TRANSLATION,
        TaskType.SUMMARIZATION,
    ]:
        # Fast/cost-effective models are highly capable for translation, extraction, and summarization
        cap_score = 0.95
    else:
        cap_score = 0.70

    # Escalation factor: if prior confidence is low or uncertain, boost high-capacity models
    escalation_boost = 0.0
    if prior_confidence in [ConfidenceLevel.LOW, ConfidenceLevel.UNCERTAIN]:
        if profile.max_context_tokens >= 32000:
            escalation_boost = 0.15

    # 2. Availability & Reliability Score (0.0 to 1.0)
    avail_score = 1.0 if profile.is_available else 0.1
    # Penalize based on failure rate
    if profile.total_calls > 0:
        failure_rate = profile.failure_count / profile.total_calls
        avail_score = max(0.0, avail_score - failure_rate * 0.5)

    # 3. Cost Score (0.0 to 1.0, 1.0 = free / minimal cost)
    # Free local model (Ollama) gets 1.0; cheaper models get near 1.0
    total_cost_per_1k = profile.cost_per_1k_prompt_tokens_usd + profile.cost_per_1k_completion_tokens_usd
    if total_cost_per_1k == 0.0:
        cost_score = 1.0
    else:
        # Scale cost relative to a baseline of $0.002 / 1k tokens
        cost_score = max(0.1, 1.0 - min(1.0, total_cost_per_1k / 0.002))

    # 4. Latency Score (0.0 to 1.0, 1.0 = ultra fast <300ms)
    typical_lat = profile.typical_latency_ms or 500.0
    if preferred_max_latency_ms and typical_lat > preferred_max_latency_ms:
        latency_score = 0.2
    else:
        latency_score = max(0.1, 1.0 - min(1.0, typical_lat / 2000.0))

    # Composite weighted score
    composite = (
        (WEIGHT_CAPABILITY * (cap_score + escalation_boost))
        + (WEIGHT_AVAILABILITY * avail_score)
        + (WEIGHT_COST * cost_score)
        + (WEIGHT_LATENCY * latency_score)
    )

    return {
        "model_id": profile.model_id,
        "provider": profile.provider.value,
        "composite_score": round(composite, 4),
        "breakdown": {
            "capability_score": round(cap_score, 3),
            "escalation_boost": round(escalation_boost, 3),
            "availability_score": round(avail_score, 3),
            "cost_score": round(cost_score, 3),
            "latency_score": round(latency_score, 3),
        },
        "weights": {
            "weight_capability": WEIGHT_CAPABILITY,
            "weight_availability": WEIGHT_AVAILABILITY,
            "weight_cost": WEIGHT_COST,
            "weight_latency": WEIGHT_LATENCY,
        },
    }
