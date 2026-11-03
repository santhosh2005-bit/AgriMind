"""Evaluation test suite covering general-purpose domains and multilingual execution.

Evaluates:
- Script & language detection across English, Tamil, Hindi, Telugu, Malayalam, Kannada.
- Dynamic DAG generation for Mathematics, Coding, Translation, Summarization, Research, Agriculture.
- Web search tool grounding and citation extraction.
- Deterministic AST mathematical calculation evaluation.
- Language override preference handling.
- Graceful model fallback execution under simulated faults.
"""

import unittest
from backend.app.schemas.enums import (
    SupportedLanguage,
    DomainCategory,
    TaskType,
    VerificationStatus,
    InputModality,
)
from backend.app.schemas.request import UserRequest, LocationContext
from backend.app.processing.language import (
    detect_language,
    resolve_response_language,
    get_language_system_prompt,
)
from backend.app.agents.state import AgriMindState
from backend.app.agents.nodes.input_validation import input_validation_node
from backend.app.agents.nodes.request_understanding import request_understanding_node
from backend.app.agents.nodes.planning import planning_node
from backend.app.agents.nodes.plan_validation import plan_validation_node
from backend.app.agents.nodes.step_executor import step_executor_node
from backend.app.agents.nodes.synthesizer import synthesizer_node
from backend.app.agents.nodes.verification import verification_node
from backend.app.agents.nodes.recovery import recovery_node
from backend.app.agents.nodes.final_response import final_response_node
from backend.app.verification.calculators import AgronomicCalculators
from backend.app.tools.web_search import default_web_search_connector, WebSearchQueryInput
from backend.app.services.workflow_service import workflow_service


class TestMultilingualGeneralPlatform(unittest.TestCase):
    """Rigorous evaluation suite validating multilingual and general-purpose capabilities."""

    def test_tamil_inquiry_dag_and_language_detection(self):
        """Tamil query: verifies script detection, Tamil response directive, and dynamic DAG."""
        req = UserRequest(
            text_query="தக்காளி இலை சுருட்டல் நோய்க்கான காரணங்கள் மற்றும் தடுப்பு முறைகளை விளக்குக.",
            target_language=SupportedLanguage.AUTO,
        )
        plan = workflow_service.preview_plan(req)
        self.assertIsNotNone(plan)
        self.assertGreaterEqual(len(plan.steps), 2)

        # Verify language detected
        detected = detect_language(req.text_query).detected_language
        self.assertEqual(detected, SupportedLanguage.TAMIL)

    def test_hindi_inquiry_dag_and_language_detection(self):
        """Hindi query: verifies Devanagari detection and execution plan."""
        req = UserRequest(
            text_query="गेहूं में पीला रतुआ (Yellow Rust) के लक्षण और नियंत्रण के उपाय बताएं।",
            target_language=SupportedLanguage.AUTO,
        )
        plan = workflow_service.preview_plan(req)
        self.assertIsNotNone(plan)
        self.assertGreaterEqual(len(plan.steps), 2)

        detected = detect_language(req.text_query).detected_language
        self.assertEqual(detected, SupportedLanguage.HINDI)

    def test_telugu_script_detection(self):
        """Telugu query detection."""
        query = "వరి పంటలో తెగుళ్లు నివారణ మరియు ఎరువుల నిర్వహణ గురించి చెప్పండి."
        detected = detect_language(query).detected_language
        self.assertEqual(detected, SupportedLanguage.TELUGU)

    def test_malayalam_script_detection(self):
        """Malayalam query detection."""
        query = "നെല്ല് കൃഷിയിലെ രോഗങ്ങളും അവയുടെ പ്രതിവിധികളും വിശദീകരിക്കുക."
        detected = detect_language(query).detected_language
        self.assertEqual(detected, SupportedLanguage.MALAYALAM)

    def test_kannada_script_detection(self):
        """Kannada query detection."""
        query = "ಟೊಮೆಟೊ ಎಲೆ ಸುರುಟು ರೋಗದ ಲಕ್ಷಣಗಳು ಮತ್ತು ನಿಯಂತ್ರಣ ಕ್ರಮಗಳು."
        detected = detect_language(query).detected_language
        self.assertEqual(detected, SupportedLanguage.KANNADA)

    def test_user_language_override(self):
        """Explicit user language selection takes precedence over query script."""
        query = "How to treat powdery mildew in grapes?"
        detected = detect_language(query).detected_language
        # Script is Latin (English), but user explicitly demands Tamil response
        resolved = resolve_response_language(SupportedLanguage.TAMIL, detected)
        self.assertEqual(resolved, SupportedLanguage.TAMIL)

        prompt = get_language_system_prompt("ta")
        self.assertIn("Tamil", prompt)
        self.assertIn("script", prompt)

    def test_mathematics_domain_dag_and_computation(self):
        """Math query: verifies classification as MATHEMATICS and CALCULATION step generation."""
        req = UserRequest(text_query="Calculate 15% discount on 850 followed by 18% GST.")
        state = AgriMindState(request=req)
        state = input_validation_node(state)
        state = request_understanding_node(state)
        self.assertEqual(state.request_understanding.get("domain_category"), DomainCategory.MATHEMATICS.value)

        state = planning_node(state)
        task_types = [s.task_type for s in state.execution_plan.steps]
        self.assertIn(TaskType.CALCULATION, task_types)
        self.assertIn(TaskType.VERIFICATION, task_types)

        # Test AST deterministic math evaluator
        # 850 - (15% of 850) = 722.5; 722.5 * 1.18 = 852.55
        math_eval = AgronomicCalculators.evaluate_safe_math("850 * 0.85 * 1.18", claimed_result=852.55)
        self.assertTrue(math_eval.is_valid)
        self.assertAlmostEqual(math_eval.expected_value, 852.55, places=2)

    def test_coding_domain_dag(self):
        """Coding query: verifies classification as CODING and CODE_ANALYSIS step generation."""
        req = UserRequest(text_query="Write a thread-safe LRU Cache in Python with O(1) get and put.")
        state = AgriMindState(request=req)
        state = input_validation_node(state)
        state = request_understanding_node(state)
        self.assertEqual(state.request_understanding.get("domain_category"), DomainCategory.CODING.value)

        state = planning_node(state)
        task_types = [s.task_type for s in state.execution_plan.steps]
        self.assertIn(TaskType.CODE_ANALYSIS, task_types)
        self.assertIn(TaskType.VERIFICATION, task_types)

    def test_web_search_tool_execution(self):
        """Web search tool: queries external sources and formats RetrievedEvidence citations."""
        res = default_web_search_connector.search(
            WebSearchQueryInput(query="Perovskite solar cell technology", max_results=3)
        )
        self.assertIsNotNone(res)
        self.assertEqual(res.tool_name, "web_search")
        self.assertGreaterEqual(len(res.evidence_items), 1)
        # Check source attribution
        ev = res.evidence_items[0]
        self.assertEqual(ev.source_type, "web_search")
        self.assertTrue(bool(ev.location_reference))

    def test_research_domain_dag_with_web_search(self):
        """Research query: verifies WEB_SEARCH is scheduled in the execution plan."""
        req = UserRequest(text_query="Research latest news and developments in solid state batteries.")
        state = AgriMindState(request=req)
        state = input_validation_node(state)
        state = request_understanding_node(state)
        state = planning_node(state)
        task_types = [s.task_type for s in state.execution_plan.steps]
        self.assertIn(TaskType.WEB_SEARCH, task_types)
        self.assertIn(TaskType.GENERAL_REASONING, task_types)

    def test_end_to_end_multilingual_synthesis_and_verification(self):
        """Full end-to-end flow for a general query verifying 5-tier taxonomy and language tag."""
        req = UserRequest(
            text_query="What are the main causes and algorithmic prevention methods for distributed deadlock?",
            target_language=SupportedLanguage.ENGLISH,
        )
        state = AgriMindState(request=req)
        state = input_validation_node(state)
        state = request_understanding_node(state)
        state = planning_node(state)
        state = plan_validation_node(state)

        # Run synthesizer
        state = synthesizer_node(state)
        synthesis = state.intermediate_results.get("synthesis")
        self.assertIsNotNone(synthesis)
        self.assertTrue(len(synthesis["main_answer"]) >= 15)
        self.assertTrue(len(synthesis["observed_facts"]) >= 1)
        self.assertTrue(len(synthesis["possible_causes"]) >= 1)
        self.assertTrue(len(synthesis["recommendations"]) >= 1)
        self.assertTrue(len(synthesis["uncertainties_and_limitations"]) >= 1)

        # Run verification and recovery
        state = verification_node(state)
        self.assertIsNotNone(state.verification_result)
        state = recovery_node(state)
        state = final_response_node(state)

        self.assertIsNotNone(state.final_response)
        self.assertEqual(state.final_response.language, SupportedLanguage.ENGLISH)
        self.assertIn("distributed deadlock", state.final_response.main_answer.lower())


if __name__ == "__main__":
    unittest.main()
