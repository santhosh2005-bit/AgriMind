"""Workflow execution service coordinator."""

import logging
from typing import Dict, Any, Optional

from backend.app.schemas.request import UserRequest
from backend.app.schemas.response import FinalResponse
from backend.app.schemas.plan import ExecutionPlan
from backend.app.agents.state import AgriMindState
from backend.app.agents.graph import agrimind_workflow

logger = logging.getLogger("agrimind.service.workflow")


class WorkflowService:
    """Coordinates execution of inquiries across the compiled LangGraph agent workflow."""

    def __init__(self, workflow=None):
        self.workflow = workflow or agrimind_workflow

    def run(self, request: UserRequest) -> AgriMindState:
        """
        Executes end-to-end multi-model, multimodal workflow for an inquiry.
        """
        logger.info(f"Initiating workflow run for request ID '{request.request_id}'")

        initial_state = AgriMindState(request=request)

        # Execute through compiled LangGraph with state dictionary
        final_state_dict = self.workflow.invoke(initial_state.model_dump())

        # Reconstruct into typed AgriMindState
        if isinstance(final_state_dict, dict):
            final_state = AgriMindState(**final_state_dict)
        else:
            final_state = final_state_dict

        # Automatically persist trace to SQLite database
        try:
            from backend.app.database.db import SessionLocal, DatabaseRepository
            with SessionLocal() as db_session:
                DatabaseRepository.save_execution_trace(final_state, db_session)
        except Exception as e:
            logger.warning(f"Could not persist trace to database: {str(e)}")

        logger.info(
            f"Workflow run completed for '{request.request_id}'. "
            f"Trace: {final_state.trace.trace_id}, StepsExecuted: {final_state.trace.total_steps_executed}"
        )
        return final_state

    def preview_plan(self, request: UserRequest) -> ExecutionPlan:
        """
        Generates only the execution plan without executing subsequent model steps.
        """
        from backend.app.agents.nodes.input_validation import input_validation_node
        from backend.app.agents.nodes.request_understanding import request_understanding_node
        from backend.app.agents.nodes.planning import planning_node
        from backend.app.agents.nodes.plan_validation import plan_validation_node

        state = AgriMindState(request=request)
        state = input_validation_node(state)
        state = request_understanding_node(state)
        state = planning_node(state)
        state = plan_validation_node(state)

        if not state.execution_plan:
            raise ValueError("Failed to formulate execution plan.")

        return state.execution_plan


# Shared service singleton
workflow_service = WorkflowService()
