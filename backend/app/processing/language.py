"""Multilingual processing, language detection, and target language prompt resolution."""

import re
from typing import Dict, Tuple, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.enums import SupportedLanguage


class LanguageDetectionResult(BaseModel):
    """Result of language and script analysis."""
    detected_language: SupportedLanguage
    script_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    is_indic: bool = False
    character_counts: Dict[str, int] = Field(default_factory=dict)


# Unicode codepoint ranges for supported South Asian scripts
INDIC_SCRIPT_RANGES: Dict[str, Tuple[int, int, SupportedLanguage]] = {
    "Tamil": (0x0B80, 0x0BFF, SupportedLanguage.TAMIL),
    "Devanagari": (0x0900, 0x097F, SupportedLanguage.HINDI),
    "Telugu": (0x0C00, 0x0C7F, SupportedLanguage.TELUGU),
    "Kannada": (0x0C80, 0x0CFF, SupportedLanguage.KANNADA),
    "Malayalam": (0x0D00, 0x0D7F, SupportedLanguage.MALAYALAM),
}

# Common transliterated / Romanized markers
HINGLISH_MARKERS = {
    "kya", "hai", "kaise", "karein", "patte", "peele", "dawai", "rog", "kisan",
    "paani", "lag", "gaya", "khet", "fasal", "kitna", "chahiye"
}
TANGLISH_MARKERS = {
    "enna", "pannunga", "solunga", "ilai", "maram", "thani", "marundhu",
    "eppadi", "irukku", "agum", "seyya", "vendum"
}


def detect_language(text: str) -> LanguageDetectionResult:
    """
    Deterministically detects natural language and script from input text.
    Zero-dependency, sub-millisecond execution leveraging Unicode codepoints.
    """
    if not text or not text.strip():
        return LanguageDetectionResult(
            detected_language=SupportedLanguage.ENGLISH,
            script_name="Unknown",
            confidence=0.5,
            is_indic=False,
        )

    clean_text = text.strip()
    counts: Dict[str, int] = {script: 0 for script in INDIC_SCRIPT_RANGES}
    latin_count = 0
    total_alpha = 0

    for ch in clean_text:
        cp = ord(ch)
        if ch.isalpha():
            total_alpha += 1
            if 0x0041 <= cp <= 0x005A or 0x0061 <= cp <= 0x007A:
                latin_count += 1
                continue

            for script, (start, end, _) in INDIC_SCRIPT_RANGES.items():
                if start <= cp <= end:
                    counts[script] += 1
                    break

    if total_alpha == 0:
        return LanguageDetectionResult(
            detected_language=SupportedLanguage.ENGLISH,
            script_name="NonAlphabetic",
            confidence=0.5,
            is_indic=False,
            character_counts=counts,
        )

    # 1. Check for native Indic script characters
    highest_script = max(counts, key=counts.get)
    highest_count = counts[highest_script]

    if highest_count > 0:
        script_ratio = highest_count / total_alpha
        target_lang = INDIC_SCRIPT_RANGES[highest_script][2]
        confidence = min(1.0, max(0.70, round(script_ratio + 0.15, 2)))
        return LanguageDetectionResult(
            detected_language=target_lang,
            script_name=highest_script,
            confidence=confidence,
            is_indic=True,
            character_counts=counts,
        )

    # 2. Check for Romanized / Transliterated text
    words = set(re.findall(r"\b[a-z]+\b", clean_text.lower()))
    hinglish_overlap = len(words.intersection(HINGLISH_MARKERS))
    tanglish_overlap = len(words.intersection(TANGLISH_MARKERS))

    if hinglish_overlap >= 2:
        return LanguageDetectionResult(
            detected_language=SupportedLanguage.HINDI,
            script_name="Romanized-Devanagari",
            confidence=0.80,
            is_indic=True,
            character_counts={"latin": latin_count, "hinglish_tokens": hinglish_overlap},
        )

    if tanglish_overlap >= 2:
        return LanguageDetectionResult(
            detected_language=SupportedLanguage.TAMIL,
            script_name="Romanized-Tamil",
            confidence=0.80,
            is_indic=True,
            character_counts={"latin": latin_count, "tanglish_tokens": tanglish_overlap},
        )

    # 3. Default to English
    return LanguageDetectionResult(
        detected_language=SupportedLanguage.ENGLISH,
        script_name="Latin",
        confidence=0.95,
        is_indic=False,
        character_counts={"latin": latin_count},
    )


def resolve_response_language(
    user_preference: Optional[SupportedLanguage],
    detected_lang: SupportedLanguage
) -> SupportedLanguage:
    """
    Resolves the final target delivery language:
    - If user explicitly selected a language (e.g. Tamil), prioritizes that.
    - If AUTO or unspecified, matches the detected inquiry language.
    """
    if user_preference and user_preference != SupportedLanguage.AUTO:
        return user_preference
    return detected_lang if detected_lang != SupportedLanguage.AUTO else SupportedLanguage.ENGLISH


def get_language_system_prompt(target_lang: SupportedLanguage) -> str:
    """
    Produces explicit system instruction to ensure native fluency while
    preserving technical accuracy, scientific citations, units, and code blocks.
    """
    instructions = {
        SupportedLanguage.TAMIL: (
            "LANGUAGE REQUIREMENT: Respond entirely in natural, fluent Tamil (தமிழ்).\n"
            "- Use proper Tamil script and colloquial clarity where appropriate.\n"
            "- PRESERVE in English / standard notation: mathematical formulas, programming code, "
            "chemical compounds (e.g. N, P, K, Urea), numbers (e.g. 120 kg/ha), and URLs/citations.\n"
            "- Do not output transliterated English unless requested."
        ),
        SupportedLanguage.HINDI: (
            "LANGUAGE REQUIREMENT: Respond entirely in natural, fluent Hindi (हिंदी).\n"
            "- Use proper Devanagari script.\n"
            "- PRESERVE in English / standard notation: mathematical formulas, code blocks, "
            "chemical notations, numbers, and official document/citation IDs.\n"
            "- Do not output Romanized Hinglish."
        ),
        SupportedLanguage.TELUGU: (
            "LANGUAGE REQUIREMENT: Respond entirely in natural, fluent Telugu (తెలుగు).\n"
            "- Use proper Telugu script.\n"
            "- PRESERVE in standard notation: mathematical formulas, numbers, chemical terms, code, and source citations."
        ),
        SupportedLanguage.MALAYALAM: (
            "LANGUAGE REQUIREMENT: Respond entirely in natural, fluent Malayalam (മലയാളം).\n"
            "- Use proper Malayalam script.\n"
            "- PRESERVE in standard notation: code, formulas, units, numbers, and source citations."
        ),
        SupportedLanguage.KANNADA: (
            "LANGUAGE REQUIREMENT: Respond entirely in natural, fluent Kannada (ಕನ್ನಡ).\n"
            "- Use proper Kannada script.\n"
            "- PRESERVE in standard notation: code, mathematical formulas, units, numbers, and source citations."
        ),
        SupportedLanguage.ENGLISH: (
            "LANGUAGE REQUIREMENT: Respond in clear, precise English."
        ),
        SupportedLanguage.AUTO: (
            "LANGUAGE REQUIREMENT: Respond in the same language as the user's primary inquiry."
        ),
    }
    return instructions.get(target_lang, instructions[SupportedLanguage.ENGLISH])
