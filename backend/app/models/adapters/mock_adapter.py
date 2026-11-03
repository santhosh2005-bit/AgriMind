"""Deterministic mock adapter for offline testing, CI, and local development."""

import json
import time
import re
from typing import List, Optional, Dict, Any, Type
from pydantic import BaseModel

from backend.app.schemas.enums import InputModality, TaskType, ModelProvider, DeploymentType
from backend.app.schemas.routing import ModelProfile
from backend.app.models.base import BaseModelAdapter, ModelResponse


class MockAdapter(BaseModelAdapter):
    """
    Simulates model responses with realistic agronomic domain content.
    Clearly marks outputs with `is_mock=True` to never fabricate live execution.
    """

    def __init__(self, model_id: str = "mock-agri-model", display_name: str = "Mock Development Adapter"):
        profile = ModelProfile(
            model_id=model_id,
            display_name=display_name,
            provider=ModelProvider.MOCK,
            deployment_type=DeploymentType.MOCK_LOCAL,
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
            max_context_tokens=8192,
            supports_structured_output=True,
            supports_vision=True,
            supports_tool_calling=True,
            cost_per_1k_prompt_tokens_usd=0.0,
            cost_per_1k_completion_tokens_usd=0.0,
            typical_latency_ms=120.0,
            is_available=True,
            timeout_seconds=5,
        )
        super().__init__(profile)

    def check_availability(self) -> bool:
        return True

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

        prompt_lower = prompt.lower()
        has_images = bool(images and len(images) > 0)

        # Context-aware mock responses based on prompt keywords and domains
        # 1. Agricultural context (Highest priority for AgriMind)
        if any(w in prompt_lower for w in ["tomato", "leaf", "crop", "soil", "pest", "fertiliz", "agronomic", "curl", "plant"]):
            if "tamil" in prompt_lower or " ta" in prompt_lower or "தமிழ்" in prompt_lower:
                content = (
                    "தக்காளி பயிர் (Tomato Crop) இலை மஞ்சள் நிறமாதல் மற்றும் சுருட்டல் தொடர்பான வேளாண் ஆலோசனை:\n\n"
                    "1. கவனிக்கப்பட்ட அறிகுறிகள்: தக்காளி இலைகளில் நரம்புகளுக்கு இடைப்பட்ட மஞ்சள் நிறமாதல் (Interveinal Chlorosis) மற்றும் மேல்நோக்கிய சுருட்டல் அறிகுறிகள் காணப்படுகின்றன.\n"
                    "2. சாத்தியமான காரணங்கள்: அதிக வெப்பநிலை மற்றும் குறைந்த ஈரப்பதம் காரணமாக ஏற்படும் வெப்ப அழுத்தம், அல்லது வெள்ளீ ஈக்களால் பரவும் தக்காளி இலை சுருட்டல் வைரஸ் (TYLCV).\n"
                    "3. பரிந்துரைக்கப்படும் நடைமுறை நடவடிக்கைகள்:\n"
                    "   • ஏக்கருக்கு 15-20 மஞ்சள் ஒட்டும் பொறிகளை (Yellow Sticky Traps) அமைத்து வெள்ளீ ஈக்களின் நடமாட்டத்தை கண்காணிக்கவும்.\n"
                    "   • அதிக வெப்பத்தைத் தணிக்க அதிகாலை வேளையில் சீரான சொட்டு நீர் பாசனம் வழங்கவும்.\n"
                    "   • மண் பரிசோதனை அறிக்கையின்படி காரத்தன்மை (pH 7.8) மற்றும் உப்புத்தன்மை உள்ளதால் பரிந்துரைக்கப்பட்ட ஜிப்சம் மற்றும் நுண்ணூட்டச்சத்து கலவையை இடவும்.\n"
                    "   • அறிகுறிகள் தீவிரமடைந்தால் மாதிரி இலைகளை அருகிலுள்ள வேளாண் அறிவியல் மையத்திற்கு (KVK) ஆய்வுக்கு அனுப்பவும்."
                )
            elif "hindi" in prompt_lower or " hi" in prompt_lower:
                content = (
                    "टमाटर की फसल में पत्तियों के पीलेपन और मुड़ने पर कृषि सलाह:\n"
                    "1. लक्षण: पत्तियों पर पीलापन (क्लोरोसिस) और ऊपर की ओर मुड़ना।\n"
                    "2. संभावित कारण: उच्च तापमान या सफेद मक्खी (Whitefly) द्वारा फैलने वाला पर्ण कुंचन वायरस (TYLCV)।\n"
                    "3. सुझाव: प्रति हेक्टेयर 15-20 पीले चिपचिपे ट्रैप लगाएं, सुबह के समय ड्रिप सिंचाई करें और सूक्ष्म पोषक तत्वों का छिड़काव करें।"
                )
            else:
                content = (
                    "Agronomic Diagnostic Summary:\n"
                    "Observed foliar chlorosis and upward leaf curling on tomato plants evaluated alongside local meteorological telemetry "
                    "indicates either Tomato Yellow Leaf Curl Virus (TYLCV) or physiological leaf rolling caused by daytime thermal stress (>34°C).\n"
                    "Actionable Steps:\n"
                    "1. Install yellow sticky traps (15-20 per hectare) to monitor whitefly vector populations.\n"
                    "2. Schedule morning drip irrigation to alleviate transpirational heat stress.\n"
                    "3. Apply soil amendments per soil test (pH 7.8) and consult local KVK extension officers."
                )
        elif re.search(r"\b(python|javascript|typescript|c\+\+|java|rust|algorithm|def |class )\b", prompt_lower):
            content = (
                "```python\ndef solution(items: list) -> list:\n    \"\"\"General-purpose algorithmic processing.\"\"\"\n"
                "    return sorted(items)\n```\n\nCode analyzed and validated with deterministic edge cases."
            )
        elif re.search(r"\b(calculate|math|integral|percentage|arithmetic)\b", prompt_lower):
            content = (
                "Mathematical Reasoning & Computation:\n"
                "1. Formulate problem equations.\n"
                "2. Evaluate numerical constraints.\n"
                "3. Verified calculation result: Consistent."
            )
        elif re.search(r"\b(translate|translation|in tamil|in hindi)\b", prompt_lower):
            content = (
                "Multilingual Translation Output:\n"
                "Faithfully translated into target language while preserving technical terms, numbers, and formulas."
            )
        elif "summar" in prompt_lower:
            content = (
                "Executive Summary:\n"
                "- Core concept extracted and organized.\n"
                "- Key takeaways and action points structured."
            )
        elif "search" in prompt_lower or "research" in prompt_lower:
            content = (
                "Research Findings & Evidence Grounding:\n"
                "Retrieved relevant public information and verified citations across multiple sources."
            )
        elif has_images or "leaf" in prompt_lower or "photo" in prompt_lower:
            content = (
                "Tomato Foliar Symptom Analysis (Mock Demonstration):\n"
                "- Observed upward curling along the leaflet margins.\n"
                "- Interveinal chlorosis (yellowing) visible on upper canopy leaves.\n"
                "- No conspicuous necrotic lesions observed on stems.\n"
                "Note: Visual inspection indicates symptoms consistent with viral (e.g. TYLCV) or heat-stress disorders, "
                "but laboratory testing is required for definitive diagnosis."
            )
        elif "plan" in prompt_lower or "steps" in prompt_lower:
            content = (
                "Execution Plan Formulation (Mock Demonstration):\n"
                "Step 1: Inspect input and identify intent.\n"
                "Step 2: Retrieve relevant guidelines or execute computation.\n"
                "Step 3: Synthesize findings.\n"
                "Step 4: Verify accuracy and output schema."
            )
        elif "weather" in prompt_lower:
            content = (
                "Weather Correlation Summary (Mock Demonstration):\n"
                "Recent meteorological conditions indicate elevated temperatures (34°C - 36°C) "
                "and depressed relative humidity (<35%), creating favorable conditions for vector proliferation."
            )
        else:
            content = (
                "Agronomic Intelligence Synthesis (Mock Demonstration):\n"
                "Based on the observed foliar curling and high ambient temperature, possible causes include "
                "Tomato Yellow Leaf Curl Virus (TYLCV) or physiological leaf roll induced by thermal stress. "
                "Immediate field inspection for whitefly populations and irrigation checks are recommended."
            )

        # Simulate structured output if schema requested
        structured_data: Optional[Dict[str, Any]] = None
        if response_schema is not None:
            # Construct a basic schema-compatible mock dictionary
            structured_data = {
                "summary": "Mock structured response for development testing",
                "content": content,
                "confidence": "medium",
                "is_mock": True,
            }

        latency_ms = round((time.perf_counter() - start_time) * 1000 + 45.0, 2)
        prompt_tokens = max(10, len(prompt.split()) * 2)
        completion_tokens = max(10, len(content.split()) * 2)
        total_tokens = prompt_tokens + completion_tokens

        self.stats.record_call(latency_ms=latency_ms, tokens=total_tokens, cost_usd=0.0, success=True)

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
            is_mock=True,
            raw_metadata={"simulated": True, "task_prompt_preview": prompt[:80]},
        )
