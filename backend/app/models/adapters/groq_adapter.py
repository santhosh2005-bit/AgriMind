"""Groq commercial model adapter (Category B: Commercial Model 2 - Fast Hosted Inference)."""

import json
import time
from typing import List, Optional, Dict, Any, Type
from pydantic import BaseModel

from backend.app.schemas.enums import InputModality, TaskType, ModelProvider, DeploymentType
from backend.app.schemas.routing import ModelProfile
from backend.app.models.base import BaseModelAdapter, ModelResponse
from backend.app.core.config import settings


class GroqAdapter(BaseModelAdapter):
    """
    Adapter for Groq Cloud (e.g. llama-3.3-70b-versatile).
    Specialized for high-throughput reasoning, complex planning, JSON mode, and fast synthesis.
    """

    def __init__(self, model_id: Optional[str] = None, api_key: Optional[str] = None):
        selected_model = model_id or settings.GROQ_DEFAULT_MODEL
        self.api_key = api_key or settings.GROQ_API_KEY

        profile = ModelProfile(
            model_id=selected_model,
            display_name=f"Groq {selected_model}",
            provider=ModelProvider.GROQ,
            deployment_type=DeploymentType.COMMERCIAL_CLOUD,
            supported_modalities=[InputModality.TEXT],  # Explicitly text-only: distinguishes capabilities from assumptions
            supported_task_types=[
                TaskType.INPUT_VALIDATION,
                TaskType.REQUEST_UNDERSTANDING,
                TaskType.PLANNING,
                TaskType.AGRICULTURAL_REASONING,
                TaskType.RESULT_SYNTHESIS,
                TaskType.VERIFICATION,
                TaskType.RECOVERY,
                TaskType.GENERAL_REASONING,
                TaskType.TRANSLATION,
                TaskType.SUMMARIZATION,
                TaskType.CALCULATION,
                TaskType.CODE_ANALYSIS,
            ],
            max_context_tokens=131072,  # 128k context
            supports_structured_output=True,
            supports_vision=False,      # Explicitly False
            supports_tool_calling=True,
            cost_per_1k_prompt_tokens_usd=0.00059,     # $0.59 / 1M tokens
            cost_per_1k_completion_tokens_usd=0.00079, # $0.79 / 1M tokens
            typical_latency_ms=320.0,
            is_available=bool(self.api_key and self.api_key != "your_groq_api_key_here"),
            timeout_seconds=20,
        )
        super().__init__(profile)
        self._client = None

    def check_availability(self) -> bool:
        if not self.api_key or self.api_key == "your_groq_api_key_here":
            return False
        return True

    def _get_client(self):
        if self._client is None and self.check_availability():
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        return self._client

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

        # Reject image modality if passed
        if images and len(images) > 0:
            raise ValueError(f"Model {self.profile.model_id} on Groq does not support image modality.")

        # Fallback to mock if API key not present and mock fallback enabled
        if not self.check_availability():
            if settings.ENABLE_MOCK_FALLBACKS_FOR_TESTS:
                from backend.app.models.adapters.mock_adapter import MockAdapter
                mock = MockAdapter(model_id=f"mock-{self.profile.model_id}")
                res = mock.generate(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    response_schema=response_schema,
                )
                res.raw_metadata["fallback_reason"] = "Groq API key not configured; using transparent test mock"
                return res
            raise ValueError("GROQ_API_KEY is not configured and mock fallback is disabled.")

        try:
            client = self._get_client()
            messages: List[Dict[str, str]] = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            kwargs: Dict[str, Any] = {
                "model": self.profile.model_id,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            if response_schema:
                kwargs["response_format"] = {"type": "json_object"}

            completion = None
            last_err = None
            for attempt in range(3):
                try:
                    completion = client.chat.completions.create(**kwargs)
                    break
                except Exception as ex:
                    last_err = ex
                    if "429" in str(ex) or "rate_limit" in str(ex).lower():
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    raise ex
            if completion is None and last_err is not None:
                raise last_err

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            choice = completion.choices[0]
            content = choice.message.content or ""

            prompt_tokens = getattr(completion.usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(completion.usage, "completion_tokens", 0) or 0
            total_tokens = getattr(completion.usage, "total_tokens", prompt_tokens + completion_tokens)

            cost_usd = self.estimate_cost(prompt_tokens, completion_tokens)
            self.stats.record_call(latency_ms, total_tokens, cost_usd, success=True)

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
                estimated_cost_usd=cost_usd,
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
                res.raw_metadata["fallback_reason"] = f"Groq call failed ({str(e)}); used mock fallback"
                return res
            raise RuntimeError(f"Groq API generation failed: {str(e)}") from e
