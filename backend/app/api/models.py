"""Model registry management and connectivity test endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.schemas.routing import ModelProfile
from backend.app.models.registry import default_registry
from backend.app.models.base import ModelResponse

router = APIRouter(prefix="/v1/models", tags=["Model Registry"])


class ModelTestRequest(BaseModel):
    model_id: str = Field(..., description="Target model ID to test")
    prompt: str = Field(default="Provide a brief one-sentence definition of integrated pest management.")
    system_instruction: Optional[str] = Field(default="You are an agricultural intelligence assistant.")


class ModelTestResponse(BaseModel):
    model_id: str
    provider: str
    is_mock: bool
    latency_ms: float
    total_tokens: int
    estimated_cost_usd: float
    content: str
    metadata: dict


@router.get("", response_model=List[ModelProfile])
def list_registered_models():
    """
    List all models currently registered in the AgriMind registry.
    Never exposes API keys or credentials.
    """
    return default_registry.list_profiles()


@router.post("/test-call", response_model=ModelTestResponse)
def test_model_connection(req: ModelTestRequest):
    """
    Invoke a quick test generation on a registered model to verify credentials and latency.
    """
    if not default_registry.has_model(req.model_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{req.model_id}' is not registered."
        )

    adapter = default_registry.get_adapter(req.model_id)
    try:
        response: ModelResponse = adapter.generate(
            prompt=req.prompt,
            system_instruction=req.system_instruction,
        )
        return ModelTestResponse(
            model_id=response.model_id,
            provider=response.provider.value,
            is_mock=response.is_mock,
            latency_ms=response.latency_ms,
            total_tokens=response.total_tokens,
            estimated_cost_usd=response.estimated_cost_usd,
            content=response.content,
            metadata=response.raw_metadata,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Model test invocation failed: {str(e)}"
        )
