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
        crop_name = "Crop"
        crop_tamil = "பயிர்"
        crop_hindi = "फसल"
        crop_map = {
            "carrot": ("Carrot", "கேரட்", "गाजर"),
            "கேரட்": ("Carrot", "கேரட்", "गाजर"),
            "गाजर": ("Carrot", "கேரட்", "गाजर"),
            "tomato": ("Tomato", "தக்காளி", "टमाटर"),
            "தக்காளி": ("Tomato", "தக்காளி", "टमाटर"),
            "टमाटर": ("Tomato", "தக்காளி", "टमाटर"),
            "potato": ("Potato", "உருளைக்கிழங்கு", "आलू"),
            "onion": ("Onion", "வெங்காயம்", "प्याज"),
            "chilli": ("Chilli", "மிளகாய்", "मिर्च"),
            "paddy": ("Paddy", "நெல்", "धान"),
            "rice": ("Paddy", "நெல்", "धान"),
            "wheat": ("Wheat", "கோதுமை", "गेहूं"),
        }
        for token, (c_en, c_ta, c_hi) in crop_map.items():
            if token in prompt_lower:
                crop_name = c_en
                crop_tamil = c_ta
                crop_hindi = c_hi
                break

        if any(w in prompt_lower for w in ["crop", "soil", "pest", "fertiliz", "agronomic", "curl", "plant", "carrot", "tomato", "potato", "onion", "தோட்டம்", "கேரட்", "தக்காளி", "பயிர்", "பண்ணை"]):
            if "tamil" in prompt_lower or " ta" in prompt_lower or "தமிழ்" in prompt_lower or any(0x0B80 <= ord(c) <= 0x0BFF for c in prompt):
                content = (
                    f"{crop_tamil} பயிர் ({crop_name} Crop) தொடர்பான விரிவான வேளாண் கள ஆய்வு மற்றும் மேலாண்மை வழிகாட்டல்:\n\n"
                    f"1. கவனிக்கப்பட்ட கள அறிகுறிகள்: {crop_tamil} பயிரில் இலை மஞ்சள் நிறமாதல், வளர்ச்சி குன்றிய நிலை மற்றும் ஈரப்பத அழுத்த அறிகுறிகள் பதிவு செய்யப்பட்டுள்ளன.\n"
                    f"2. சாத்தியமான காரணங்கள்: அதிகப்படியான ஈரப்பதம்/மழைப்பொழிவு காரணமாக ஏற்படும் பூஞ்சை தொற்று (Fungal pathogens) அல்லது மண்ணில் ஊட்டச்சத்து சமநிலையின்மை (Nutrient deficiency).\n"
                    f"3. பரிந்துரைக்கப்படும் நடைமுறை நடவடிக்கைகள்:\n"
                    f"   • தோட்டத்தில் நீர் தேங்குவதைத் தடுத்து சீரான வடிகால் வசதியை ஏற்படுத்தவும்.\n"
                    f"   • பாதிக்கப்பட்ட தாவர பகுதிகளை அகற்றி சுத்தமான கள சுகாதாரம் பேணவும்.\n"
                    f"   • பரிந்துரைக்கப்பட்ட பாதுகாப்பான பூஞ்சாணக்கொல்லி (Mancozeb அல்லது Copper Oxychloride) தெளித்து பாதுகாக்கவும்.\n"
                    f"   • மண் பரிசோதனை பரிந்துரைகளின்படி நுண்ணூட்டச்சத்து மற்றும் தழைச்சத்து மேலாண்மை செய்யவும்.\n"
                    f"   • அறிகுறிகள் தீவிரமடைந்தால் மாதிரி பகுதிகளை அருகிலுள்ள வேளாண் அறிவியல் மையத்திற்கு (KVK) ஆய்வுக்கு அனுப்பவும்."
                )
            elif "hindi" in prompt_lower or " hi" in prompt_lower or any(0x0900 <= ord(c) <= 0x097F for c in prompt):
                content = (
                    f"{crop_hindi} की फसल ({crop_name} Crop) में रोग एवं पोषक तत्व प्रबंधन पर व्यापक कृषि सलाह:\n\n"
                    f"1. प्रेक्षित लक्षण: {crop_hindi} की पत्तियों में पीलापन और कवक संक्रमण के संकेत।\n"
                    f"2. संभावित कारण: अत्यधिक नमी या जलभराव के कारण फफूंद जनित रोग और पोषक तत्वों का असंतुलन।\n"
                    f"3. अनुशंसित कार्य योजना:\n"
                    f"   • खेत में उचित जल निकासी की व्यवस्था करें।\n"
                    f"   • संक्रमित पौधों को हटाकर खेत को स्वच्छ रखें।\n"
                    f"   • अनुमोदित फफूंदनाशी (मैनकोजेब या कॉपर ऑक्सीक्लोराइड) का छिड़काव करें।\n"
                    f"   • अधिक जानकारी के लिए निकटतम कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"
                )
            else:
                content = (
                    f"Comprehensive Agronomic Diagnostic & Advisory for {crop_name} Crop:\n\n"
                    f"1. Observed Field Findings: Foliar chlorosis, physiological moisture stress, and tissue vulnerability identified on {crop_name}.\n"
                    f"2. Differential Causes: Fungal dampening/root rot exacerbated by excessive humidity and precipitation, or micronutrient depletion in high-moisture soils.\n"
                    f"3. Actionable Agronomic Plan:\n"
                    f"   • Improve field drainage channels to prevent waterlogging around root zones.\n"
                    f"   • Cull decaying or blighted vegetative tissues immediately to arrest secondary spore dispersal.\n"
                    f"   • Apply protective foliar fungicide (Mancozeb 75% WP @ 2.0 g/L) during clear morning hours.\n"
                    f"   • Balance soil nutrition per local extension soil-test specifications."
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
                f"{crop_name} Foliar Symptom & Tissue Analysis:\n"
                f"- Observed morphological chlorosis and foliar stress symptoms on {crop_name} vegetative canopy.\n"
                "- Interveinal discoloration and moisture disparity visible on upper foliar regions.\n"
                "- No conspicuous acute viral necrosis observed on structural stems.\n"
                "Note: Visual inspection indicates symptoms consistent with moisture/nutrient stress or secondary pathogens. "
                "Laboratory testing recommended for definitive diagnostic confirmation."
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
