"""Health check and system status endpoints."""

from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.models.registry import default_registry

router = APIRouter(prefix="/health", tags=["System Health"])


class HealthStatusResponse(BaseModel):
    status: str
    app_name: str = "AgriMind"
    version: str = "0.1.0"
    environment: str
    timestamp: datetime
    registered_models_count: int
    models_status: Dict[str, bool]
    configuration: Dict[str, Any]


@router.get("", response_model=HealthStatusResponse)
def get_system_health():
    """Returns the operational status of the AgriMind backend, environment, and model connectivity."""
    models_status = {}
    for profile in default_registry.list_profiles():
        models_status[profile.model_id] = profile.is_available

    return HealthStatusResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
        registered_models_count=len(models_status),
        models_status=models_status,
        configuration={
            "max_plan_steps": settings.MAX_PLAN_STEPS,
            "step_timeout_sec": settings.DEFAULT_STEP_TIMEOUT_SECONDS,
            "budget_sec": settings.WORKFLOW_EXECUTION_BUDGET_SECONDS,
            "mock_fallbacks_enabled": settings.ENABLE_MOCK_FALLBACKS_FOR_TESTS,
            "gemini_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here"),
            "groq_configured": bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your_groq_api_key_here"),
            "ollama_url": settings.OLLAMA_BASE_URL,
        },
    )
