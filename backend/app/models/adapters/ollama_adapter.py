"""Ollama open-weight local model adapter (Category C: Open-Weight / Smaller Local Model)."""

import json
import time
from typing import List, Optional, Dict, Any, Type
import httpx
from pydantic import BaseModel

from backend.app.schemas.enums import InputModality, TaskType, ModelProvider, DeploymentType
from backend.app.schemas.routing import ModelProfile
from backend.app.models.base import BaseModelAdapter, ModelResponse
from backend.app.core.config import settings


class OllamaAdapter(BaseModelAdapter):
    """
    Adapter for local Ollama instance (e.g. llama3.2:3b).
    Operates completely locally with zero token cost, supporting offline privacy-first execution.
    """

    def __init__(self, model_id: Optional[str] = None, base_url: Optional[str] = None):
        selected_model = model_id or settings.OLLAMA_DEFAULT_MODEL
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")

        profile = ModelProfile(
            model_id=selected_model,
            display_name=f"Ollama {selected_model} (Local)",
            provider=ModelProvider.OLLAMA,
            deployment_type=DeploymentType.OPEN_WEIGHT_LOCAL,
            supported_modalities=[InputModality.TEXT],
            supported_task_types=[
                TaskType.INPUT_VALIDATION,
                TaskType.REQUEST_UNDERSTANDING,
                TaskType.AGRICULTURAL_REASONING,
                TaskType.RESULT_SYNTHESIS,
                TaskType.GENERAL_REASONING,
                TaskType.TRANSLATION,
                TaskType.SUMMARIZATION,
                TaskType.CALCULATION,
                TaskType.CODE_ANALYSIS,
            ],
            max_context_tokens=8192,
            supports_structured_output=True,
            supports_vision=False,
            supports_tool_calling=False,
            cost_per_1k_prompt_tokens_usd=0.0,     # Completely free local inference
            cost_per_1k_completion_tokens_usd=0.0,
            typical_latency_ms=1100.0,
            is_available=False,
            timeout_seconds=45,
        )
        super().__init__(profile)
        self._last_check_timestamp: float = 0.0
        self._cached_availability: bool = False

    def check_availability(self) -> bool:
        """Ping local Ollama daemon to check connectivity and model availability (cached 10s)."""
        now = time.time()
        if now - self._last_check_timestamp < 10.0:
            return self._cached_availability

        try:
            with httpx.Client(timeout=0.8) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    self._cached_availability = True
                    self._last_check_timestamp = now
                    return True
                self._cached_availability = False
                self._last_check_timestamp = now
                return False
        except Exception:
            self._cached_availability = False
            self._last_check_timestamp = now
            return False

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        images: Optional[List[bytes]] = None,
        response_schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        start_time = time.perf_counter()

        if images and len(images) > 0:
            raise ValueError(f"Model {self.profile.model_id} on Ollama does not support image modality.")

        # If local daemon is not running, fallback to mock if enabled
        is_up = self.check_availability()
        if not is_up:
            if settings.ENABLE_MOCK_FALLBACKS_FOR_TESTS:
                from backend.app.models.adapters.mock_adapter import MockAdapter
                mock = MockAdapter(model_id=f"mock-{self.profile.model_id}")
                res = mock.generate(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    response_schema=response_schema,
                )
                res.raw_metadata["fallback_reason"] = (
                    f"Local Ollama daemon at {self.base_url} is offline; using transparent test mock"
                )
                return res
            raise ConnectionError(f"Ollama local daemon at {self.base_url} is not reachable.")

        try:
            messages: List[Dict[str, str]] = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            payload: Dict[str, Any] = {
                "model": self.profile.model_id,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            }
            if response_schema:
                payload["format"] = "json"

            with httpx.Client(timeout=float(self.profile.timeout_seconds)) as client:
                response = client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            content = data.get("message", {}).get("content", "")

            prompt_tokens = data.get("prompt_eval_count", 0) or max(10, len(prompt.split()) * 2)
            completion_tokens = data.get("eval_count", 0) or max(10, len(content.split()) * 2)
            total_tokens = prompt_tokens + completion_tokens

            self.stats.record_call(latency_ms, total_tokens, cost_usd=0.0, success=True)

            structured_data = None
            if response_schema and content:
                try:
                    structured_data = json.loads(content)
                except Exception:
                    pass

            return ModelResponse(
                content=content,
                structured_data=structured_data,
                model_id=self.profile.model_id,
                provider=self.profile.provider,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=0.0,
                latency_ms=latency_ms,
                is_mock=False,
            )

        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.stats.record_call(latency_ms, 0, 0.0, success=False)
            if settings.ENABLE_MOCK_FALLBACKS_FOR_TESTS:
                from backend.app.models.adapters.mock_adapter import MockAdapter
                mock = MockAdapter(model_id=f"mock-{self.profile.model_id}")
                res = mock.generate(prompt=prompt, response_schema=response_schema)
                res.raw_metadata["fallback_reason"] = f"Ollama call failed ({str(e)}); used mock fallback"
                return res
            raise RuntimeError(f"Ollama local generation failed: {str(e)}") from e
