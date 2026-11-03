"""Unit tests for AgriMind Model Registry and model adapters."""

import unittest
from backend.app.schemas.enums import InputModality, TaskType, ModelProvider, DeploymentType
from backend.app.schemas.routing import ModelProfile
from backend.app.models.registry import ModelRegistry, create_default_registry
from backend.app.models.adapters.mock_adapter import MockAdapter
from backend.app.models.adapters.gemini_adapter import GeminiAdapter
from backend.app.models.adapters.groq_adapter import GroqAdapter
from backend.app.models.adapters.ollama_adapter import OllamaAdapter


class TestModelRegistry(unittest.TestCase):
    """Test model registration, capability filtering, cost estimation, and fallback logic."""

    def setUp(self):
        self.registry = create_default_registry()

    def test_default_registry_contains_required_three_categories(self):
        """Verify presence of Category A (Gemini), Category B (Groq), Category C (Ollama)."""
        profiles = self.registry.list_profiles()
        providers = {p.provider for p in profiles}

        self.assertIn(ModelProvider.GEMINI, providers, "Category A: Gemini must be registered")
        self.assertIn(ModelProvider.GROQ, providers, "Category B: Groq must be registered")
        self.assertIn(ModelProvider.OLLAMA, providers, "Category C: Ollama must be registered")

    def test_capability_distinction_for_vision(self):
        """
        Problem requirement: Distinguish model capabilities from assumptions.
        Only Gemini (or vision-capable models) should match when IMAGE modality is required.
        Groq (Llama 3.3 70B text) and Ollama (Llama 3.2 3B text) must be excluded.
        """
        vision_models = self.registry.find_compatible_models(
            required_modalities=[InputModality.IMAGE]
        )
        for adapter in vision_models:
            self.assertTrue(adapter.profile.supports_vision)
            self.assertIn(InputModality.IMAGE, adapter.profile.supported_modalities)

        # Groq must NOT be returned for image requests
        groq_in_vision = any(a.profile.provider == ModelProvider.GROQ for a in vision_models)
        self.assertFalse(groq_in_vision, "Groq text model must not be matched for vision tasks")

    def test_cost_estimation_calculation(self):
        """Verify cost estimation calculation using provider rate cards."""
        from backend.app.core.config import settings
        groq_adapter = self.registry.get_adapter(settings.GROQ_DEFAULT_MODEL)
        cost = groq_adapter.estimate_cost(prompt_tokens=1000, completion_tokens=1000)
        self.assertGreaterEqual(cost, 0.0)

        ollama_adapter = self.registry.get_adapter(settings.OLLAMA_DEFAULT_MODEL)
        # Ollama local inference has zero cost
        self.assertEqual(ollama_adapter.estimate_cost(5000, 5000), 0.0)

    def test_mock_adapter_generation(self):
        """Verify mock adapter produces realistic output and records latency statistics."""
        mock = MockAdapter()
        res = mock.generate(prompt="What are the symptoms of tomato leaf curl virus?")
        self.assertTrue(res.is_mock)
        self.assertGreater(res.latency_ms, 0)
        self.assertGreater(res.total_tokens, 0)
        self.assertIn("Tomato", res.content)

        # Stats should be recorded
        self.assertEqual(mock.stats.total_calls, 1)
        self.assertGreater(mock.stats.average_latency_ms, 0)

    def test_fallback_resolution(self):
        """Ensure a fallback model is found when primary model is specified."""
        from backend.app.core.config import settings
        fallback = self.registry.get_fallback_for(settings.GROQ_DEFAULT_MODEL)
        self.assertIsNotNone(fallback)
        self.assertNotEqual(fallback.profile.model_id, settings.GROQ_DEFAULT_MODEL)


if __name__ == "__main__":
    unittest.main()
