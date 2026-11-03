"""Workflow execution and plan preview endpoints."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.schemas.request import UserRequest
from backend.app.schemas.response import FinalResponse
from backend.app.schemas.plan import ExecutionPlan
from backend.app.schemas.trace import ExecutionTrace
from backend.app.schemas.verification import VerificationResult
from backend.app.services.workflow_service import workflow_service

router = APIRouter(prefix="/v1/workflow", tags=["Agentic Workflow"])


class WorkflowRunResponse(BaseModel):
    final_response: FinalResponse
    execution_plan: Optional[ExecutionPlan] = None
    verification_result: Optional[VerificationResult] = None
    trace: ExecutionTrace
    execution_errors: list[str] = Field(default_factory=list)


@router.post("/run", response_model=WorkflowRunResponse)
def execute_workflow(request: UserRequest):
    """
    Executes the complete LangGraph agentic workflow for an agricultural inquiry:
    1. Input validation & request understanding.
    2. Dynamic conditional planning.
    3. Multi-model routing & tool execution.
    4. Synthesis, deterministic verification & critic.
    5. Final structured response with source citations.
    """
    try:
        final_state = workflow_service.run(request)
        if not final_state.final_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Workflow completed without producing a final response."
            )
        return WorkflowRunResponse(
            final_response=final_state.final_response,
            execution_plan=final_state.execution_plan,
            verification_result=final_state.verification_result,
            trace=final_state.trace,
            execution_errors=final_state.execution_errors,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/plan", response_model=ExecutionPlan)
def preview_plan(request: UserRequest):
    """
    Generate and preview the conditional execution plan without executing steps.
    """
    try:
        return workflow_service.preview_plan(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan formulation failed: {str(e)}"
        )
