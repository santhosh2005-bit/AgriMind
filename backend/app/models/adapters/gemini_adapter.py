"""Google Gemini commercial model adapter (Category A: Commercial Model 1 - Vision & Multimodal)."""

import io
import time
from typing import List, Optional, Dict, Any, Type
from pydantic import BaseModel
from PIL import Image

from backend.app.schemas.enums import InputModality, TaskType, ModelProvider, DeploymentType
from backend.app.schemas.routing import ModelProfile
from backend.app.models.base import BaseModelAdapter, ModelResponse
from backend.app.core.config import settings


class GeminiAdapter(BaseModelAdapter):
    """
    Adapter for Google Gemini (e.g. gemini-1.5-flash).
    Provides multimodal comprehension (text + images) and structured generation.
    """

    def __init__(self, model_id: Optional[str] = None, api_key: Optional[str] = None):
        selected_model = model_id or settings.GEMINI_DEFAULT_MODEL
        self.api_key = api_key or settings.GEMINI_API_KEY

        profile = ModelProfile(
            model_id=selected_model,
            display_name=f"Google {selected_model}",
            provider=ModelProvider.GEMINI,
            deployment_type=DeploymentType.COMMERCIAL_CLOUD,
            supported_modalities=[InputModality.TEXT, InputModality.IMAGE],
            supported_task_types=[
                TaskType.INPUT_VALIDATION,
                TaskType.REQUEST_UNDERSTANDING,
                TaskType.PLANNING,
                TaskType.VISION_ANALYSIS,
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
            max_context_tokens=1048576,  # 1M token context
            supports_structured_output=True,
            supports_vision=True,
            supports_tool_calling=True,
            cost_per_1k_prompt_tokens_usd=0.000075,     # $0.075 / 1M tokens
            cost_per_1k_completion_tokens_usd=0.00030, # $0.30 / 1M tokens
            typical_latency_ms=750.0,
            is_available=bool(self.api_key and self.api_key != "your_gemini_api_key_here"),
            timeout_seconds=30,
        )
        super().__init__(profile)
        self._client_initialized = False

    def check_availability(self) -> bool:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return False
        return True

    def _init_client(self) -> bool:
        if not self.check_availability():
            return False
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client_initialized = True
            return True
        except Exception:
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

        # If API key is not configured or in test mode, safely fallback if configured
        if not self.check_availability():
            if settings.ENABLE_MOCK_FALLBACKS_FOR_TESTS:
                from backend.app.models.adapters.mock_adapter import MockAdapter
                mock = MockAdapter(model_id=f"mock-{self.profile.model_id}")
                res = mock.generate(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    images=images,
                    response_schema=response_schema,
                )
                res.raw_metadata["fallback_reason"] = "Gemini API key not configured; using transparent test mock"
                return res
            raise ValueError("GEMINI_API_KEY is not configured and mock fallback is disabled.")

        try:
            import google.generativeai as genai
            if not self._client_initialized:
                self._init_client()

            generation_config = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            model = genai.GenerativeModel(
                model_name=self.profile.model_id,
                system_instruction=system_instruction if system_instruction else None,
                generation_config=generation_config,
            )

            contents: List[Any] = []
            if images:
                for img_bytes in images:
                    img = Image.open(io.BytesIO(img_bytes))
                    contents.append(img)
            contents.append(prompt)

            response = model.generate_content(contents)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Safely extract text: response.text raises ValueError when candidates
            # are empty, blocked by safety filters, or finish_reason is not STOP.
            text_content = ""
            try:
                candidates = getattr(response, "candidates", None)
                if candidates:
                    candidate = candidates[0]
                    finish_reason = getattr(candidate, "finish_reason", None)
                    # finish_reason 1 = STOP (normal), 0 = UNSPECIFIED (treat as ok)
                    finish_reason_val = int(finish_reason) if finish_reason is not None else 1
                    if finish_reason_val in (0, 1) and hasattr(candidate, "content"):
                        parts = getattr(candidate.content, "parts", [])
                        text_content = "".join(
                            getattr(p, "text", "") for p in parts if hasattr(p, "text")
                        ).strip()
                if not text_content:
                    # Safe fallback: try the high-level .text property
                    text_content = response.text
            except (ValueError, AttributeError, IndexError):
                # Raised when candidates are blocked or empty — treat as empty response
                text_content = ""

            # Attempt token usage extraction if available
            prompt_tokens = 0
            completion_tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
            else:
                prompt_tokens = max(10, len(prompt.split()) * 2)
                completion_tokens = max(10, len(text_content.split()) * 2)

            cost_usd = self.estimate_cost(prompt_tokens, completion_tokens)
            self.stats.record_call(latency_ms, prompt_tokens + completion_tokens, cost_usd, success=True)

            return ModelResponse(
                content=text_content,
                model_id=self.profile.model_id,
                provider=self.profile.provider,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost_usd=cost_usd,
                latency_ms=latency_ms,
                is_mock=False,
            )

        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.stats.record_call(latency_ms, 0, 0.0, success=False)
            if "ResourceExhausted" in str(e) or "429" in str(e) or "quota" in str(e).lower():
                import logging
                logging.getLogger("agrimind.adapter.gemini").warning(
                    f"Gemini API free tier daily quota exhausted (20 requests/day): {str(e)}. "
                    "Failing over to secondary live model in registry (Groq Cloud)."
                )
            raise RuntimeError(f"Gemini API generation failed ({str(e)})") from e
