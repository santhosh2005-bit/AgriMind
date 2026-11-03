"""Node 2: Universal Request Understanding, Intent Extraction, and Language Detection."""

import logging
import re
from typing import Dict, Any, List
from backend.app.schemas.enums import DomainCategory, SupportedLanguage
from backend.app.processing.language import detect_language, resolve_response_language
from backend.app.agents.state import AgriMindState

logger = logging.getLogger("agrimind.node.request_understanding")

# Broad agricultural dictionary (English + vernacular Indic common names)
EXPANDED_CROP_LEXICON: Dict[str, str] = {
    # Cereals & Millets
    "wheat": "wheat", "gothumai": "wheat", "gehun": "wheat", "kanaka": "wheat",
    "rice": "rice", "paddy": "rice", "dhan": "rice", "arisi": "rice", "nel": "rice", "vari": "rice", "bhat": "rice",
    "maize": "maize", "corn": "maize", "makka": "maize", "cholam": "sorghum",
    "sorghum": "sorghum", "jowar": "sorghum", "bajra": "pearl_millet", "kambu": "pearl_millet", "ragi": "finger_millet",
    
    # Vegetables
    "tomato": "tomato", "thakkali": "tomato", "tamatar": "tomato",
    "potato": "potato", "aloo": "potato", "urulaikizhangu": "potato", "bangaladumpa": "potato",
    "onion": "onion", "pyaz": "onion", "vengayam": "onion", "ullipaya": "onion",
    "carrot": "carrot", "gajar": "carrot", "கேரட்": "carrot", "gajjara": "carrot",
    "chilli": "chilli", "chili": "chilli", "pepper": "chilli", "mirch": "chilli", "mirchi": "chilli", "milagai": "chilli",
    "brinjal": "eggplant", "eggplant": "eggplant", "baingan": "eggplant", "kathirikai": "eggplant", "vankaya": "eggplant",
    "cabbage": "cabbage", "patta gobhi": "cabbage", "cauliflower": "cauliflower", "phool gobhi": "cauliflower",
    "garlic": "garlic", "lehsun": "garlic", "poondu": "garlic", "ginger": "ginger", "adrak": "ginger", "inji": "ginger",
    
    # Commercial & Cash Crops
    "cotton": "cotton", "kapas": "cotton", "paruthi": "cotton", "prathi": "cotton",
    "sugarcane": "sugarcane", "ganna": "sugarcane", "karumbu": "sugarcane", "cheruku": "sugarcane",
    "soybean": "soybean", "soya": "soybean",
    "tea": "tea", "chai": "tea", "coffee": "coffee", "kaapi": "coffee", "rubber": "rubber",
    "tobacco": "tobacco", "tambaku": "tobacco", "pogaku": "tobacco",
    
    # Fruits & Horticulture
    "pomegranate": "pomegranate", "anar": "pomegranate", "madhulai": "pomegranate", "danimma": "pomegranate",
    "mango": "mango", "aam": "mango", "mambazham": "mango", "mamidi": "mango",
    "banana": "banana", "kela": "banana", "vazhai": "banana", "arati": "banana",
    "grape": "grape", "grapes": "grape", "angur": "grape", "drakshi": "grape", "draksha": "grape",
    "citrus": "citrus", "orange": "citrus", "santre": "citrus", "lemon": "lemon", "nimbu": "lemon", "elumichai": "lemon",
    "apple": "apple", "seb": "apple", "papaya": "papaya", "papita": "papaya", "pappali": "papaya",
    "guava": "guava", "amrood": "guava", "koyya": "guava",
    
    # Pulses & Oilseeds
    "mustard": "mustard", "sarson": "mustard", "kadugu": "mustard", "aavalu": "mustard",
    "groundnut": "groundnut", "peanut": "groundnut", "moongphali": "groundnut", "verukadalai": "groundnut",
    "chickpea": "chickpea", "gram": "chickpea", "chana": "chickpea", "kadalai": "chickpea",
    "pigeonpea": "pigeonpea", "arhar": "pigeonpea", "tur": "pigeonpea", "tuvar": "pigeonpea", "thuvaram": "pigeonpea",
    "blackgram": "blackgram", "urad": "blackgram", "ulundu": "blackgram", "greengram": "greengram", "moong": "greengram",
}


def classify_domain(query_lower: str, detected_indic: bool) -> DomainCategory:
    """Classifies user inquiry into functional domain categories."""
    # 1. Agriculture (Priority domain: crops, soil, pests, fertilizers, irrigation, symptoms, farms, gardens)
    agri_patterns = [
        r"\b(crop|crops|farm|farms|farmer|farmers|farming|field|fields|orchard|plantation|plot|acre|acres|hectare|parcel)\b",
        r"\b(soil|soils|fertilizer|fertiliser|urea|dap|npk|pesticide|fungicide|herbicide|weed|blight|rust|rot|wilt)\b",
        r"\b(irrigation|harvest|sowing|yield|pruning|grafting|pest|infestation|chlorosis|leaf curl|ph |salinity|yellow leaves|leaves|plant|plants)\b",
        r"\b(carrot|carrots|tomato|tomatoes|potato|potatoes|onion|onions|vegetable|vegetables|pulse|pulses|grain|grains)\b",
        r"(விவசாயம்|பயிர்|விதை|உரம்|மருந்து|நோய்|பூச்சி|பாசனம்|தோட்டம்|பண்ணை|விவசாயி|கேரட்)",
        r"(कृषि|फसल|खाद|उर्वरक|कीट|रोग|छिड़काव|सिंचाई|मिट्टी|खेत|किसान|गाजर)",
    ]
    has_agri_keyword = any(re.search(pat, query_lower) for pat in agri_patterns)
    has_crop_mention = any(crop_token in query_lower for crop_token in EXPANDED_CROP_LEXICON)

    if has_agri_keyword or has_crop_mention:
        return DomainCategory.AGRICULTURE

    # 2. Coding & Debugging
    code_patterns = [
        r"\b(python|javascript|typescript|c\+\+|java|rust|golang|sql|html|css)\b",
        r"\b(function|def |class |async |await |return |import |variable|bug|debug|algorithm)\b",
        r"\b(binary tree|array|linked list|sorting|regex|api endpoint|docker|git)\b",
    ]
    if any(re.search(pat, query_lower) for pat in code_patterns):
        return DomainCategory.CODING

    # 3. Mathematics & Calculations
    math_patterns = [
        r"\b(calculate|integral|derivative|equation|algebra|geometry|matrix|eigenvalue)\b",
        r"\b(percentage|compound interest|emi|logarithm|factorial|probability)\b",
        r"[\d\.]+\s*[\+\-\*\/\^]\s*[\d\.]+",  # arithmetic expressions like "45 * 128"
    ]
    if any(re.search(pat, query_lower) for pat in math_patterns):
        return DomainCategory.MATHEMATICS

    # 4. Translation (Explicit translation requests only)
    translation_patterns = [
        r"\b(translate\b|translation of|how do you say .* in|to english|to tamil|to hindi|to telugu)\b",
        r"\b(மொழிபெயர்|अनुवाद|భాషాంతరీకరణ|అనువాదం)\b",
    ]
    if any(re.search(pat, query_lower) for pat in translation_patterns):
        return DomainCategory.TRANSLATION

    # 5. Summarization
    summary_patterns = [
        r"\b(summarize|summary|summarise|briefly explain|tldr|key takeaways|executive summary)\b",
        r"\b(சுருக்கம்|सारांश|సారాంశం)\b",
    ]
    if any(re.search(pat, query_lower) for pat in summary_patterns):
        return DomainCategory.SUMMARIZATION

    # 6. External Research & Web Search
    research_patterns = [
        r"\b(who is|latest news|current price|stock price|who won|current prime minister|president of|when was .* founded)\b",
        r"\b(headquarters of|weather forecast for next 14 days|current gdp)\b",
    ]
    if any(re.search(pat, query_lower) for pat in research_patterns):
        return DomainCategory.RESEARCH
    # Default to general knowledge explanation
    return DomainCategory.GENERAL_KNOWLEDGE


def request_understanding_node(state: AgriMindState) -> AgriMindState:
    """
    Parses natural language query to identify:
    - Input language and script (via deterministic Unicode detection)
    - Domain category (Agriculture, General Knowledge, Math, Coding, Translation, Research)
    - Target delivery language (respecting user preference or auto-matching)
    - Crop species, observed symptoms, weather intent, and missing information.
    """
    logger.info("Executing Universal Request Understanding Node")
    raw_query = state.request.text_query.strip()
    query_lower = raw_query.lower()

    # 1. Multilingual Detection & Language Resolution
    lang_det = detect_language(raw_query)
    target_lang = resolve_response_language(
        user_preference=state.request.target_language,
        detected_lang=lang_det.detected_language,
    )
    state.request.detected_language = lang_det.detected_language

    # 2. Domain Classification
    domain_category = classify_domain(query_lower, detected_indic=lang_det.is_indic)
    # Default to AGRICULTURE if location is given or image is uploaded and it's not coding or math
    if domain_category == DomainCategory.GENERAL_KNOWLEDGE and (state.request.location or InputModality.IMAGE in state.detected_modalities):
        domain_category = DomainCategory.AGRICULTURE

    # 3. Detect crop mentions (for agricultural inquiries)
    detected_crops = []
    for token, canonical in EXPANDED_CROP_LEXICON.items():
        if re.search(r"\b" + re.escape(token) + r"\b", query_lower):
            if canonical not in detected_crops:
                detected_crops.append(canonical)

    primary_crop = detected_crops[0] if detected_crops else "unspecified_crop"

    # 4. Check for weather intent
    weather_keywords = ["weather", "temperature", "humidity", "rain", "rainfall", "climate", "frost", "drought", "வானிலை", "मौसम", "వాతావరణం"]
    has_weather_intent = any(k in query_lower for k in weather_keywords) or bool(state.request.location)

    # 5. Check for disease / symptom intent
    symptom_keywords = [
        "curl", "curling", "yellow", "yellowing", "spot", "wilt", "blight", "rot", "pest", "disease", "symptom",
        "சுருட்டை", "மஞ்சள்", "புள்ளி", "அழுகல்", "வாடல்", "कीट", "मरोड़िया", "धब्बा", "सड़न", "झुलसा"
    ]
    has_symptom_intent = any(s in query_lower for s in symptom_keywords)

    # 6. Missing information analysis
    missing_info: List[str] = []
    if domain_category == DomainCategory.AGRICULTURE:
        if has_weather_intent and not state.request.location:
            missing_info.append("Geographic location (coordinates or city name) is missing for weather telemetry.")
        if not detected_crops and has_symptom_intent:
            missing_info.append("Specific crop species not explicitly mentioned in query.")

    state.request_understanding = {
        "domain_category": domain_category.value,
        "primary_crop": primary_crop,
        "detected_crops": detected_crops,
        "detected_language": lang_det.detected_language.value,
        "target_language": target_lang.value,
        "script_name": lang_det.script_name,
        "is_indic": lang_det.is_indic,
        "has_weather_intent": has_weather_intent,
        "has_symptom_intent": has_symptom_intent,
        "missing_information": missing_info,
        "user_constraints": state.request.constraints,
    }

    logger.info(
        f"Request understanding completed: Domain='{domain_category.value}', "
        f"Lang='{lang_det.detected_language.value}' -> Target='{target_lang.value}', "
        f"Crop='{primary_crop}', MissingInfoCount={len(missing_info)}"
    )
    return state
