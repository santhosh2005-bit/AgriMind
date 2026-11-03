"""Trace exploration, execution history, and user feedback endpoints."""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.db import get_db, DatabaseRepository

logger = logging.getLogger("agrimind.api.traces")

router = APIRouter(tags=["Telemetry & History"])


class FeedbackRequest(BaseModel):
    run_id: str = Field(..., description="Target execution run ID")
    rating: int = Field(..., ge=1, le=5, description="1 to 5 star rating")
    is_helpful: bool = Field(default=True, description="Whether the recommendation was helpful")
    comment: Optional[str] = Field(None, description="Detailed farmer or evaluator comments")


class FeedbackResponse(BaseModel):
    status: str = "success"
    feedback_id: str
    message: str


@router.get("/v1/traces/{trace_id}")
async def get_execution_trace(
    trace_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve full execution trace for a given run ID, including plan DAG steps,
    model routing decisions, token usage, costs in USD, tools, evidence, and verification.
    """
    trace_data = DatabaseRepository.get_run_trace(trace_id, db)
    if not trace_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution trace with ID '{trace_id}' not found.",
        )
    return trace_data


@router.get("/v1/history/runs")
async def list_execution_runs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    crop: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    """
    Returns a paginated list of historical advisory execution runs with summary metrics.
    """
    runs = DatabaseRepository.list_runs(
        db=db,
        limit=limit,
        offset=offset,
        crop=crop,
        status=status_filter,
    )
    return {
        "count": len(runs),
        "limit": limit,
        "offset": offset,
        "runs": runs,
    }


@router.post("/v1/history/feedback", response_model=FeedbackResponse)
async def submit_user_feedback(
    body: FeedbackRequest,
    db: Session = Depends(get_db),
):
    """
    Submit user ratings and comments on advisory recommendations to support continuous evaluation.
    """
    run = DatabaseRepository.get_run_trace(body.run_id, db)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution run '{body.run_id}' not found for attaching feedback.",
        )

    fb = DatabaseRepository.add_user_feedback(
        db=db,
        run_id=body.run_id,
        rating=body.rating,
        is_helpful=body.is_helpful,
        comment=body.comment,
    )

    return FeedbackResponse(
        feedback_id=fb.feedback_id,
        message="Thank you! Feedback recorded successfully.",
    )
