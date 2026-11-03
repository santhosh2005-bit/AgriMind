"""Unit tests for AgriMind core Pydantic schemas."""

import unittest
from datetime import datetime
from uuid import uuid4

from backend.app.schemas import (
    InputModality,
    TaskType,
    ModelProvider,
    DeploymentType,
    StepStatus,
    ToolStatus,
    VerificationStatus,
    ConfidenceLevel,
    InputMetadata,
    LocationContext,
    UserRequest,
    PlanStep,
    ExecutionPlan,
    ModelProfile,
    RoutingDecision,
    RetrievedEvidence,
    ToolInvocation,
    ToolResult,
    VerificationCheck,
    ConfidenceBreakdown,
    VerificationResult,
    ModelCallRecord,
    RecoveryEvent,
    ExecutionTrace,
    SourceReference,
    FinalResponse,
)


class TestAgriMindSchemas(unittest.TestCase):
    """Verify validation, serialization, and constraints of core schemas."""

    def test_user_request_valid(self):
        req = UserRequest(
            text_query="Why are my tomato leaves curling and yellowing?",
            location=LocationContext(place_name="Nashik, India", latitude=19.9975, longitude=73.7898),
            inputs=[
                InputMetadata(
                    modality=InputModality.IMAGE,
                    filename="tomato_leaf_symptom.jpg",
                    mime_type="image/jpeg",
                    file_size_bytes=245000,
                )
            ],
        )
        self.assertEqual(req.text_query, "Why are my tomato leaves curling and yellowing?")
        self.assertIn(InputModality.IMAGE, req.get_modalities())
        self.assertIn(InputModality.TEXT, req.get_modalities())

    def test_user_request_empty_query_fails(self):
        with self.assertRaises(ValueError):
            UserRequest(text_query="   ")

    def test_plan_and_steps_dag(self):
        step1 = PlanStep(
            step_number=1,
            title="Image Symptom Analysis",
            description="Examine leaf chlorosis and curling",
            task_type=TaskType.VISION_ANALYSIS,
            required_modalities=[InputModality.IMAGE],
            assigned_model_id="gemini-1.5-flash",
            status=StepStatus.COMPLETED,
        )
        step2 = PlanStep(
            step_number=2,
            title="Weather Retrieval",
            description="Fetch past 14-day humidity and temperature",
            task_type=TaskType.WEATHER_RETRIEVAL,
            assigned_tool_name="weather_connector",
            dependencies=[step1.step_id],
            status=StepStatus.PENDING,
        )
        plan = ExecutionPlan(
            request_id="req-123",
            steps=[step1, step2],
            rationale="Conditional execution: inspect image first, then query weather for suspected fungal conditions.",
        )
        executable = plan.get_executable_steps()
        self.assertEqual(len(executable), 1)
        self.assertEqual(executable[0].step_id, step2.step_id)

    def test_routing_decision(self):
        decision = RoutingDecision(
            step_id="step-1",
            task_type=TaskType.VISION_ANALYSIS,
            selected_model_id="gemini-1.5-flash",
            selected_provider=ModelProvider.GEMINI,
            rationale="Selected Gemini 1.5 Flash due to native vision understanding and low latency.",
            fallback_model_id="llama-3.3-70b-versatile",
            fallback_provider=ModelProvider.GROQ,
            decision_factors={"modality_match": 1.0, "latency_score": 0.9, "cost_weight": 0.8},
        )
        self.assertEqual(decision.selected_provider, ModelProvider.GEMINI)
        self.assertFalse(decision.is_fallback)

    def test_tool_result_and_evidence(self):
        evidence = RetrievedEvidence(
            source_type="advisory_pdf",
            source_name="ICAR_Tomato_Guide_2024.pdf",
            location_pointer="Page 14, Section 3.2",
            content_snippet="Tomato yellow leaf curl virus is transmitted by Bemisia tabaci whiteflies under hot, dry conditions.",
            relevance_score=0.92,
        )
        result = ToolResult(
            invocation_id="inv-456",
            tool_name="agricultural_retriever",
            status=ToolStatus.SUCCESS,
            structured_data={"match_count": 1},
            evidence_items=[evidence],
            latency_ms=142.5,
        )
        self.assertEqual(len(result.evidence_items), 1)
        self.assertEqual(result.evidence_items[0].source_name, "ICAR_Tomato_Guide_2024.pdf")

    def test_verification_result(self):
        check = VerificationCheck(
            check_type="deterministic_calculation",
            status=VerificationStatus.PASSED,
            details="Verified N-P-K ratio calculation in soil analysis using Python math.",
            deterministic_passed=True,
        )
        verif = VerificationResult(
            overall_status=VerificationStatus.PASSED,
            checks=[check],
            confidence=ConfidenceBreakdown(
                evidence_coverage_score=0.88,
                data_completeness_score=0.95,
                overall_confidence=ConfidenceLevel.HIGH,
                heuristic_score=0.90,
            ),
        )
        self.assertEqual(verif.passed_count, 1)
        self.assertEqual(verif.failed_count, 0)

    def test_final_response_schema_completeness(self):
        """Verify all fields required by Section 9 of problem statement."""
        res = FinalResponse(
            request_id="req-test-999",
            request_summary="Tomato leaf curling and weather correlation",
            main_answer="The observed leaf curl symptoms combined with high temperature indicate possible Tomato Yellow Leaf Curl Virus.",
            observed_facts=["Leaf margin upward curling observed in provided image."],
            retrieved_evidence=[
                RetrievedEvidence(
                    source_type="weather_api",
                    source_name="Open-Meteo",
                    content_snippet="Max daily temp 36°C with 30% relative humidity over past 10 days.",
                )
            ],
            possible_causes=["Tomato Yellow Leaf Curl Virus (TYLCV)", "Heat stress-induced physiological leaf roll"],
            recommendations=[
                "Inspect undersides of leaves for whitefly presence.",
                "Consult local Krishi Vigyan Kendra (KVK) officer for field testing.",
            ],
            uncertainties_and_limitations=[
                "Visual analysis alone cannot definitively confirm viral presence without PCR or ELISA testing."
            ],
            source_references=[
                SourceReference(
                    title="ICAR Tomato Disease Advisory",
                    location_pointer="Bulletin No. 42",
                    citation_text="TYLCV vectors proliferate when temps exceed 32C.",
                )
            ],
            verification_status=VerificationStatus.PASSED_WITH_LIMITATIONS,
            trace_id="trace-abc-123",
        )
        # Check serialization round-trip
        data = res.model_dump()
        self.assertIn("observed_facts", data)
        self.assertIn("possible_causes", data)
        self.assertIn("uncertainties_and_limitations", data)
        self.assertIn("source_references", data)
        self.assertIn("verification_status", data)


if __name__ == "__main__":
    unittest.main()
