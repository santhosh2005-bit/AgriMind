"""Unit tests for multilingual detection, script analysis, and prompt formulation."""

import unittest
from backend.app.schemas.enums import SupportedLanguage
from backend.app.processing.language import (
    detect_language,
    resolve_response_language,
    get_language_system_prompt,
)


class TestLanguageProcessing(unittest.TestCase):
    """Verifies multilingual detection across all 6 target languages."""

    def test_tamil_detection(self):
        query = "தக்காளி இலைகளில் மஞ்சள் புள்ளிகள் மற்றும் சுருட்டை நோய் உள்ளது என்ன மருந்து தெளிக்க வேண்டும்?"
        res = detect_language(query)
        self.assertEqual(res.detected_language, SupportedLanguage.TAMIL)
        self.assertEqual(res.script_name, "Tamil")
        self.assertTrue(res.is_indic)
        self.assertGreaterEqual(res.confidence, 0.85)

    def test_hindi_detection(self):
        query = "टमाटर के पत्तों में पीलापन और मरोड़िया रोग के लक्षण दिख रहे हैं कौन सी दवा डालें?"
        res = detect_language(query)
        self.assertEqual(res.detected_language, SupportedLanguage.HINDI)
        self.assertEqual(res.script_name, "Devanagari")
        self.assertTrue(res.is_indic)
        self.assertGreaterEqual(res.confidence, 0.85)

    def test_telugu_detection(self):
        query = "టమాటా ఆకులపై పసుపు మచ్చలు మరియు ముడుచుకునే లక్షణాలు ఉన్నాయి నివారణ ఏమిటి?"
        res = detect_language(query)
        self.assertEqual(res.detected_language, SupportedLanguage.TELUGU)
        self.assertEqual(res.script_name, "Telugu")
        self.assertTrue(res.is_indic)
        self.assertGreaterEqual(res.confidence, 0.85)

    def test_kannada_detection(self):
        query = "ಟೊಮೆಟೊ ಎಲೆಗಳಲ್ಲಿ ಹಳದಿ ಕಲೆಗಳು ಮತ್ತು ಸುರುಳಿ ರೋಗದ ಲಕ್ಷಣಗಳಿವೆ ಯಾವ ಔಷಧಿ ಸಿಂಪಡಿಸಬೇಕು?"
        res = detect_language(query)
        self.assertEqual(res.detected_language, SupportedLanguage.KANNADA)
        self.assertEqual(res.script_name, "Kannada")
        self.assertTrue(res.is_indic)
        self.assertGreaterEqual(res.confidence, 0.85)

    def test_malayalam_detection(self):
        query = "തക്കാളി ഇലകളിൽ മഞ്ഞപ്പും ചുരുളലും കാണുന്നു എന്താണ് പ്രതിവിധി?"
        res = detect_language(query)
        self.assertEqual(res.detected_language, SupportedLanguage.MALAYALAM)
        self.assertEqual(res.script_name, "Malayalam")
        self.assertTrue(res.is_indic)
        self.assertGreaterEqual(res.confidence, 0.85)

    def test_english_detection(self):
        query = "What is the recommended nitrogen fertilizer schedule for wheat with 120 kg N per hectare?"
        res = detect_language(query)
        self.assertEqual(res.detected_language, SupportedLanguage.ENGLISH)
        self.assertEqual(res.script_name, "Latin")
        self.assertFalse(res.is_indic)
        self.assertGreaterEqual(res.confidence, 0.90)

    def test_romanized_hinglish_detection(self):
        query = "Tamatar ke patte peele ho rahe hain kaunsi dawai dalein kisan bhai"
        res = detect_language(query)
        self.assertEqual(res.detected_language, SupportedLanguage.HINDI)
        self.assertTrue(res.is_indic)

    def test_romanized_tanglish_detection(self):
        query = "Thakkali ilai la manja thitti irukku enna marundhu podalam solunga"
        res = detect_language(query)
        self.assertEqual(res.detected_language, SupportedLanguage.TAMIL)
        self.assertTrue(res.is_indic)

    def test_resolve_response_language_user_preference(self):
        # User explicitly asked for Tamil, even if query was in English
        target = resolve_response_language(
            user_preference=SupportedLanguage.TAMIL,
            detected_lang=SupportedLanguage.ENGLISH,
        )
        self.assertEqual(target, SupportedLanguage.TAMIL)

    def test_resolve_response_language_auto_detection(self):
        # User left it on AUTO, detected Hindi -> delivery should be Hindi
        target = resolve_response_language(
            user_preference=SupportedLanguage.AUTO,
            detected_lang=SupportedLanguage.HINDI,
        )
        self.assertEqual(target, SupportedLanguage.HINDI)

    def test_get_language_system_prompt_all_languages(self):
        for lang in [
            SupportedLanguage.TAMIL,
            SupportedLanguage.HINDI,
            SupportedLanguage.TELUGU,
            SupportedLanguage.KANNADA,
            SupportedLanguage.MALAYALAM,
            SupportedLanguage.ENGLISH,
        ]:
            prompt = get_language_system_prompt(lang)
            self.assertIn("LANGUAGE REQUIREMENT", prompt)
            if lang != SupportedLanguage.ENGLISH:
                self.assertIn("PRESERVE", prompt)


if __name__ == "__main__":
    unittest.main()
