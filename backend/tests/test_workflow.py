"""Unit and end-to-end integration tests for LangGraph agentic workflow."""

import unittest
from backend.app.schemas.enums import InputModality, TaskType, VerificationStatus
from backend.app.schemas.request import UserRequest, InputMetadata, LocationContext
from backend.app.agents.state import AgriMindState
from backend.app.agents.nodes.input_validation import input_validation_node
from backend.app.agents.nodes.request_understanding import request_understanding_node
from backend.app.agents.nodes.planning import planning_node
from backend.app.agents.nodes.plan_validation import plan_validation_node
from backend.app.services.workflow_service import workflow_service


class TestLangGraphWorkflow(unittest.TestCase):
    """Test dynamic planning, conditional execution, DAG validation, and end-to-end execution."""

    def test_text_only_request_conditional_planning(self):
        """
        Problem requirement: Do not execute every node unnecessarily.
        A text-only question must NOT schedule vision analysis.
        """
        req = UserRequest(
            text_query="What is the recommended nitrogen fertilizer schedule for wheat during crown root initiation?",
        )
        plan = workflow_service.preview_plan(req)

        task_types = [s.task_type for s in plan.steps]
        self.assertNotIn(TaskType.VISION_ANALYSIS, task_types, "Vision step must NOT be scheduled for text-only inquiry")
        self.assertIn(TaskType.AGRICULTURAL_REASONING, task_types)
        self.assertIn(TaskType.VERIFICATION, task_types)

    def test_multimodal_image_request_schedules_vision_step(self):
        """Image attachment must trigger a VISION_ANALYSIS step."""
        req = UserRequest(
            text_query="Analyse this crop photograph and explain possible causes of the leaf curling symptoms.",
            inputs=[
                InputMetadata(
                    modality=InputModality.IMAGE,
                    filename="tomato_leaf_curl.jpg",
                    file_size_bytes=102400,
                )
            ],
        )
        plan = workflow_service.preview_plan(req)
        task_types = [s.task_type for s in plan.steps]
        self.assertIn(TaskType.VISION_ANALYSIS, task_types, "Vision step MUST be scheduled when image is provided")

    def test_weather_request_schedules_weather_retrieval(self):
        """Weather intent and location must trigger weather retrieval step."""
        req = UserRequest(
            text_query="What are the weather risks and temperature impact on our tomato crop?",
            location=LocationContext(place_name="Nashik, Maharashtra", latitude=19.9975, longitude=73.7898),
        )
        plan = workflow_service.preview_plan(req)
        task_types = [s.task_type for s in plan.steps]
        self.assertIn(TaskType.WEATHER_RETRIEVAL, task_types)

    def test_dag_cycle_safeguard(self):
        """Safeguard: Cyclic dependencies in the DAG must be blocked by plan validation."""
        req = UserRequest(text_query="Test cyclic safeguard")
        state = AgriMindState(request=req)
        state = input_validation_node(state)
        state = request_understanding_node(state)
        state = planning_node(state)

        # Deliberately introduce a cycle in dependencies
        steps = state.execution_plan.steps
        if len(steps) >= 2:
            steps[0].dependencies = [steps[1].step_id]
            steps[1].dependencies = [steps[0].step_id]

        state = plan_validation_node(state)
        self.assertTrue(len(state.execution_errors) > 0)
        self.assertIn("Cyclic dependency detected", state.execution_errors[0])

    def test_full_workflow_end_to_end_execution(self):
        """
        Executes complete LangGraph workflow combining:
        - Text query + Image + Weather Location
        - Validates all 9 sections in FinalResponse
        - Verifies execution trace and telemetry
        """
        req = UserRequest(
            text_query="Analyse this tomato photograph, consider the weather in Nashik, and explain causes and next steps.",
            location=LocationContext(place_name="Nashik", latitude=19.99, longitude=73.79),
            inputs=[
                InputMetadata(
                    modality=InputModality.IMAGE,
                    filename="tomato_yellow_curl.jpg",
                    file_size_bytes=150000,
                )
            ],
        )

        final_state = workflow_service.run(req)

        # 1. Verification of completion
        self.assertTrue(final_state.is_completed)
        self.assertIsNotNone(final_state.final_response)

        res = final_state.final_response
        self.assertTrue("tomato" in res.main_answer.lower() or "தக்காளி" in res.main_answer)
        self.assertGreater(len(res.observed_facts), 0)
        self.assertGreater(len(res.possible_causes), 0)
        self.assertGreater(len(res.recommendations), 0)
        self.assertGreater(len(res.uncertainties_and_limitations), 0)
        self.assertGreater(len(res.source_references), 0)

        # 2. Verification status check
        self.assertIn(
            res.verification_status,
            [VerificationStatus.PASSED, VerificationStatus.PASSED_WITH_LIMITATIONS],
        )

        # 3. Telemetry and trace check
        self.assertGreater(final_state.trace.total_steps_executed, 0)
        self.assertGreater(len(final_state.trace.model_calls), 0)
        self.assertEqual(final_state.trace.request_id, req.request_id)


if __name__ == "__main__":
    unittest.main()
