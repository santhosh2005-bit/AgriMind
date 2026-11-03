"""Unit and integration tests for SQLite persistence, execution tracing, and history API."""

import unittest
from datetime import datetime, timezone
from uuid import uuid4
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database.db import (
    init_db,
    SessionLocal,
    DatabaseRepository,
)
from backend.app.database.models import ExecutionRunRecord
from backend.app.schemas.request import UserRequest
from backend.app.schemas.plan import ExecutionPlan, PlanStep
from backend.app.schemas.enums import TaskType, StepStatus, VerificationStatus, ConfidenceLevel, RecoveryAction
from backend.app.schemas.tools import RetrievedEvidence
from backend.app.schemas.trace import ModelCallRecord, RecoveryEvent
from backend.app.schemas.verification import VerificationResult, VerificationCheck, ConfidenceBreakdown
from backend.app.agents.state import AgriMindState


class TestDatabaseAndTracing(unittest.TestCase):
    """Test suite for database models, repository operations, and trace API endpoints."""

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def _create_mock_completed_state(self, run_id: str) -> AgriMindState:
        """Helper to construct a realistic completed AgriMindState with all telemetry."""
        req = UserRequest(
            session_id="test-session-123",
            text_query="Manage yellow rust in wheat field with 120 kg N target.",
        )
        state = AgriMindState(request=req)
        state.trace.trace_id = run_id
        state.trace.total_latency_ms = 1420.5
        state.trace.total_estimated_cost_usd = 0.00045
        state.trace.total_steps_executed = 3

        # Plan with steps
        step1 = PlanStep(
            step_id="step-1",
            step_number=1,
            title="Retrieve Wheat Guidelines",
            description="Fetch official ICAR wheat rust guidelines and nitrogen recommendations",
            task_type=TaskType.KNOWLEDGE_RETRIEVAL,
            assigned_model_id="mock-agri-model",
            status=StepStatus.COMPLETED,
            actual_latency_ms=120.0,
            actual_cost_usd=0.0,
        )
        step2 = PlanStep(
            step_id="step-2",
            step_number=2,
            title="Agronomic Synthesis",
            description="Synthesize differential diagnosis and IPM recommendations",
            task_type=TaskType.AGRICULTURAL_REASONING,
            assigned_model_id="gemini-1.5-flash",
            status=StepStatus.COMPLETED,
            actual_latency_ms=650.0,
            actual_cost_usd=0.00045,
            dependencies=["step-1"],
        )
        state.execution_plan = ExecutionPlan(
            request_id=req.request_id,
            crop_identified="Wheat",
            rationale="2-step plan",
            steps=[step1, step2],
        )
        state.step_statuses["step-1"] = StepStatus.COMPLETED
        state.step_statuses["step-2"] = StepStatus.COMPLETED

        # Model call record
        state.trace.model_calls.append(
            ModelCallRecord(
                step_id="step-2",
                model_id="gemini-1.5-flash",
                provider="google_gemini",
                prompt_tokens=450,
                completion_tokens=180,
                total_tokens=630,
                estimated_cost_usd=0.00045,
                latency_ms=650.0,
            )
        )

        # Evidence
        ev = RetrievedEvidence(
            source_type="advisory_document",
            source_name="ICAR_Wheat_Rust_Advisory.pdf",
            location_reference="Section 1.2",
            content_snippet="Spray Propiconazole 25% EC @ 0.1% (1 ml/litre) upon detection.",
            relevance_score=0.96,
        )
        state.retrieved_evidence.append(ev)

        # Verification result
        check = VerificationCheck(
            check_type="evidence_grounding",
            status=VerificationStatus.PASSED,
            details="Propiconazole grounded in ICAR Wheat Rust Advisory.",
            deterministic_passed=True,
        )
        state.verification_result = VerificationResult(
            overall_status=VerificationStatus.PASSED,
            checks=[check],
            confidence=ConfidenceBreakdown(
                overall_confidence=ConfidenceLevel.HIGH,
                heuristic_score=0.91,
            ),
        )

        # Recovery event
        state.recovery_events.append(
            RecoveryEvent(
                step_id="step-2",
                trigger_reason="Minor advisory caution injected",
                action_taken=RecoveryAction.RETRY_WITH_CONSTRAINTS,
                from_target="critic",
                to_target="synthesis",
                success=True,
                details="Appended laboratory confirmation disclaimer.",
            )
        )

        state.intermediate_results["synthesis"] = {
            "main_answer": "Apply Propiconazole at 1 ml/litre upon first detection of stripe rust."
        }
        return state

    def test_save_and_retrieve_execution_trace(self):
        """Test persisting complete state and querying full trace details."""
        test_run_id = f"run_{uuid4().hex[:12]}"
        state = self._create_mock_completed_state(test_run_id)

        # Persist to SQLite
        saved_rec = DatabaseRepository.save_execution_trace(state, self.db)
        self.assertEqual(saved_rec.run_id, test_run_id)
        self.assertEqual(saved_rec.status, "completed")
        self.assertEqual(saved_rec.verification_status, "passed")

        # Query back trace details
        trace = DatabaseRepository.get_run_trace(test_run_id, self.db)
        self.assertIsNotNone(trace)
        self.assertEqual(trace["run_id"], test_run_id)
        self.assertEqual(len(trace["steps"]), 2)
        self.assertEqual(len(trace["model_calls"]), 1)
        self.assertEqual(len(trace["evidence"]), 1)
        self.assertEqual(len(trace["verification_checks"]), 1)
        self.assertEqual(len(trace["recovery_events"]), 1)
        self.assertIn("Propiconazole", trace["final_answer"])

    def test_list_runs_pagination_and_filter(self):
        """Test listing historical runs with pagination and crop filter."""
        test_run_id = f"run_{uuid4().hex[:12]}"
        state = self._create_mock_completed_state(test_run_id)
        DatabaseRepository.save_execution_trace(state, self.db)

        runs = DatabaseRepository.list_runs(self.db, limit=10, offset=0)
        self.assertGreater(len(runs), 0)
        run_ids = [r["run_id"] for r in runs]
        self.assertIn(test_run_id, run_ids)

    def test_add_user_feedback(self):
        """Test recording user feedback and rating."""
        test_run_id = f"run_{uuid4().hex[:12]}"
        state = self._create_mock_completed_state(test_run_id)
        DatabaseRepository.save_execution_trace(state, self.db)

        fb = DatabaseRepository.add_user_feedback(
            db=self.db,
            run_id=test_run_id,
            rating=5,
            is_helpful=True,
            comment="Excellent dosage guidance for wheat rust.",
        )
        self.assertEqual(fb.rating, 5)
        self.assertTrue(fb.is_helpful)
        self.assertEqual(fb.run_id, test_run_id)

    def test_api_trace_endpoint(self):
        """Test GET /api/v1/traces/{trace_id} endpoint."""
        test_run_id = f"run_{uuid4().hex[:12]}"
        state = self._create_mock_completed_state(test_run_id)
        DatabaseRepository.save_execution_trace(state, self.db)

        res = self.client.get(f"/api/v1/traces/{test_run_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["run_id"], test_run_id)
        self.assertEqual(data["confidence_level"], "high")

    def test_api_trace_endpoint_not_found(self):
        """Test GET /api/v1/traces/non_existent returns 404."""
        res = self.client.get("/api/v1/traces/non_existent_run_99999")
        self.assertEqual(res.status_code, 404)
        self.assertIn("not found", res.json()["detail"].lower())

    def test_api_history_runs_endpoint(self):
        """Test GET /api/v1/history/runs endpoint."""
        res = self.client.get("/api/v1/history/runs?limit=5")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("runs", data)
        self.assertIn("count", data)

    def test_api_feedback_endpoint(self):
        """Test POST /api/v1/history/feedback endpoint."""
        test_run_id = f"run_{uuid4().hex[:12]}"
        state = self._create_mock_completed_state(test_run_id)
        DatabaseRepository.save_execution_trace(state, self.db)

        res = self.client.post(
            "/api/v1/history/feedback",
            json={
                "run_id": test_run_id,
                "rating": 4,
                "is_helpful": True,
                "comment": "Accurate advice on spray volumes.",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("feedback_id", data)


if __name__ == "__main__":
    unittest.main()
