"""Integration tests for FastAPI endpoints."""

import unittest
from fastapi.testclient import TestClient

from backend.app.main import app


class TestFastAPIEndpoints(unittest.TestCase):
    """Test system discovery, health, and model registry endpoints."""

    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["project"], "AgriMind")
        self.assertEqual(data["status"], "operational")

    def test_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertGreaterEqual(data["registered_models_count"], 3)
        self.assertIn("models_status", data)

    def test_list_models_endpoint(self):
        res = self.client.get("/api/v1/models")
        self.assertEqual(res.status_code, 200)
        models = res.json()
        self.assertIsInstance(models, list)
        self.assertGreaterEqual(len(models), 3)

        model_ids = [m["model_id"] for m in models]
        from backend.app.core.config import settings
        self.assertIn(settings.GEMINI_DEFAULT_MODEL, model_ids)
        self.assertIn(settings.GROQ_DEFAULT_MODEL, model_ids)
        self.assertIn(settings.OLLAMA_DEFAULT_MODEL, model_ids)

        # Ensure no secrets or API keys are leaked in public profile list
        for m in models:
            self.assertNotIn("api_key", m)
            self.assertNotIn("secret", m)

    def test_model_test_call_endpoint(self):
        payload = {
            "model_id": "mock-agri-model",
            "prompt": "Explain organic soil conditioning.",
        }
        res = self.client.post("/api/v1/models/test-call", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["model_id"], "mock-agri-model")
        self.assertTrue(data["is_mock"])
        self.assertGreater(data["latency_ms"], 0)
        self.assertIn("content", data)

    def test_routing_simulate_endpoint(self):
        payload = {
            "step_id": "sim-step-456",
            "task_type": "vision_analysis",
            "required_modalities": ["image", "text"],
        }
        res = self.client.post("/api/v1/routing/decide", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["step_id"], "sim-step-456")
        self.assertEqual(data["task_type"], "vision_analysis")
        self.assertIn("selected_model_id", data)
        self.assertIn("rationale", data)
        self.assertIn("decision_factors", data)

    def test_workflow_plan_endpoint(self):
        payload = {
            "text_query": "What are the common diseases affecting potato crops?",
        }
        res = self.client.post("/api/v1/workflow/plan", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("steps", data)
        self.assertGreater(len(data["steps"]), 0)
        task_types = [s["task_type"] for s in data["steps"]]
        self.assertNotIn("vision_analysis", task_types)

    def test_workflow_run_endpoint(self):
        payload = {
            "text_query": "Explain tomato leaf curl symptoms and weather impact in Pune.",
            "location": {"place_name": "Pune", "latitude": 18.52, "longitude": 73.85},
        }
        res = self.client.post("/api/v1/workflow/run", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("final_response", data)
        self.assertIn("trace", data)
        self.assertIn(data["final_response"]["verification_status"], ["passed", "passed_with_limitations"])
        self.assertGreater(len(data["final_response"]["possible_causes"]), 0)

    def test_weather_api_endpoint(self):
        payload = {"place_name": "Nashik", "latitude": 19.99, "longitude": 73.79}
        res = self.client.post("/api/v1/tools/weather", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("status", data)
        self.assertEqual(data["tool_name"], "weather_connector")

    def test_knowledge_api_endpoint(self):
        payload = {"query": "whitefly transmission of leaf curl", "crop_filter": "tomato"}
        res = self.client.post("/api/v1/tools/knowledge", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["tool_name"], "agricultural_retriever")

    def test_structured_data_api_endpoint(self):
        payload = {"crop": "Tomato"}
        res = self.client.post("/api/v1/tools/structured", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["tool_name"], "structured_data_query")


if __name__ == "__main__":
    unittest.main()
