"""Unit and integration tests for the AgriMind Capability-Aware Router and Adaptive Engine."""

import unittest
from unittest.mock import MagicMock
from backend.app.schemas.enums import (
    InputModality,
    TaskType,
    ConfidenceLevel,
    ModelProvider,
    RecoveryAction,
)
from backend.app.routing.router import ModelRouter
from backend.app.routing.engine import RoutedExecutionEngine
from backend.app.models.registry import create_default_registry
from backend.app.models.adapters.mock_adapter import MockAdapter


class TestModelRouter(unittest.TestCase):
    """Verify transparent capability matching, scoring, escalation, and fallback execution."""

    def setUp(self):
        self.registry = create_default_registry()
        self.router = ModelRouter(self.registry)
        self.engine = RoutedExecutionEngine(self.router, self.registry)

    def test_vision_task_routes_to_vision_model(self):
        """Image modality must route to a vision-capable model and reject text models."""
        decision = self.router.route_step(
            step_id="step-vision-1",
            task_type=TaskType.VISION_ANALYSIS,
            required_modalities=[InputModality.IMAGE, InputModality.TEXT],
        )
        # Winner must support vision
        winner = self.registry.get_adapter(decision.selected_model_id)
        self.assertTrue(winner.profile.supports_vision)
        self.assertIn(InputModality.IMAGE, winner.profile.supported_modalities)

        # Groq (text only) must be in excluded_candidates
        excluded = decision.decision_factors.get("excluded_candidates", {})
        from backend.app.core.config import settings
        self.assertIn(settings.GROQ_DEFAULT_MODEL, excluded)

    def test_weather_task_routes_to_deterministic_tool(self):
        """Weather queries must route to weather tool connector rather than LLM invention."""
        decision = self.router.route_step(
            step_id="step-weather-1",
            task_type=TaskType.WEATHER_RETRIEVAL,
        )
        self.assertEqual(decision.selected_model_id, "tool:weather_connector")
        self.assertTrue(decision.decision_factors.get("deterministic"))
        self.assertIn("Open-Meteo", decision.rationale)

    def test_knowledge_task_routes_to_faiss_tool(self):
        """Document queries must route to FAISS retrieval tool."""
        decision = self.router.route_step(
            step_id="step-rag-1",
            task_type=TaskType.KNOWLEDGE_RETRIEVAL,
        )
        self.assertEqual(decision.selected_model_id, "tool:faiss_retriever")
        self.assertIn("FAISS", decision.rationale)

    def test_complex_planning_favors_high_capacity_model(self):
        """Complex planning requires high context tokens and structured output when online."""
        # Simulate active commercial model online status
        from backend.app.core.config import settings
        groq_adapter = self.registry.get_adapter(settings.GROQ_DEFAULT_MODEL)
        groq_adapter.api_key = "gsk_mock_valid_key_for_test"
        groq_adapter.profile.is_available = True

        decision = self.router.route_step(
            step_id="step-plan-1",
            task_type=TaskType.PLANNING,
            required_modalities=[InputModality.TEXT],
        )
        winner = self.registry.get_adapter(decision.selected_model_id)
        # Should be a high-context commercial model (with >= 32k context)
        self.assertGreaterEqual(winner.profile.max_context_tokens, 32000)
        self.assertIn(decision.selected_model_id, [settings.GROQ_DEFAULT_MODEL, settings.GEMINI_DEFAULT_MODEL])
        self.assertIsNotNone(decision.fallback_model_id)

    def test_low_confidence_escalation(self):
        """Low prior confidence escalates capability scoring."""
        decision_normal = self.router.route_step(
            step_id="step-reason-normal",
            task_type=TaskType.AGRICULTURAL_REASONING,
            prior_confidence=ConfidenceLevel.HIGH,
        )
        decision_escalated = self.router.route_step(
            step_id="step-reason-escalated",
            task_type=TaskType.AGRICULTURAL_REASONING,
            prior_confidence=ConfidenceLevel.LOW,
        )
        self.assertIn("Escalated model tier", decision_escalated.rationale)

    def test_fallback_activation_on_primary_failure(self):
        """
        Verify that if the primary model fails, the engine logs a RecoveryEvent,
        switches to the fallback model, and successfully completes.
        """
        # Mock primary adapter to simulate an API timeout failure
        failing_adapter = MockAdapter(model_id="mock-failing-primary")
        failing_adapter.generate = MagicMock(side_effect=TimeoutError("Simulated primary model timeout"))

        backup_adapter = MockAdapter(model_id="mock-backup-success")
        backup_adapter.generate = MagicMock(return_value=MockAdapter().generate("Test backup prompt"))

        test_registry = create_default_registry()
        test_registry.register(failing_adapter)
        test_registry.register(backup_adapter)

        # Force failing model as selected and backup as fallback
        test_router = ModelRouter(test_registry)
        test_engine = RoutedExecutionEngine(test_router, test_registry)

        # Directly mock router to return failing as primary and backup as fallback
        mock_decision = test_router.route_step("step-failover-test", TaskType.AGRICULTURAL_REASONING)
        mock_decision.selected_model_id = "mock-failing-primary"
        mock_decision.fallback_model_id = "mock-backup-success"
        test_router.route_step = MagicMock(return_value=mock_decision)

        response, decision, recovery = test_engine.execute_routed_step(
            step_id="step-failover-test",
            task_type=TaskType.AGRICULTURAL_REASONING,
            prompt="Analyze soil salinity stress",
            max_retries=1,
        )

        # Verify recovery event was recorded
        self.assertIsNotNone(recovery)
        self.assertEqual(recovery.action_taken, RecoveryAction.FALLBACK_MODEL)
        self.assertEqual(recovery.from_target, "mock-failing-primary")
        self.assertEqual(recovery.to_target, "mock-backup-success")
        self.assertTrue(recovery.success)
        self.assertIsNotNone(response)


if __name__ == "__main__":
    unittest.main()
