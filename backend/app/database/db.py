"""Database connection management, session lifecycle, and repository operations."""

import json
import logging
from pathlib import Path
from typing import Generator, Dict, Any, Optional, List
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.app.core.config import settings
from backend.app.database.models import (
    Base,
    UserSessionRecord,
    ExecutionRunRecord,
    PlanStepRecord,
    ModelCallRecord,
    ToolInvocationRecord,
    EvidenceRecord,
    VerificationCheckRecord,
    RecoveryEventRecord,
    UserFeedbackRecord,
)
from backend.app.agents.state import AgriMindState

logger = logging.getLogger("agrimind.database")

# Ensure parent directory of SQLite database exists
if settings.DATABASE_URL.startswith("sqlite"):
    db_file_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    if db_file_path.startswith("./"):
        db_file_path = db_file_path[2:]
    Path(db_file_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    engine = create_engine(settings.DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes database schema and ensures all tables exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized successfully at {settings.DATABASE_URL}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseRepository:
    """Encapsulates transactional telemetry persistence and trace retrieval."""

    @staticmethod
    def save_execution_trace(state: AgriMindState, db: Session) -> ExecutionRunRecord:
        """
        Atomically persists the complete execution run, steps, model calls,
        tool invocations, evidence, verification results, and recovery events.
        """
        run_id = state.trace.trace_id or str(uuid4())
        session_id = state.request.session_id

        # 1. Ensure user session exists if session_id is provided
        if session_id:
            existing_session = db.query(UserSessionRecord).filter_by(session_id=session_id).first()
            if not existing_session:
                new_session = UserSessionRecord(
                    session_id=session_id,
                    user_metadata_json=json.dumps(state.request.user_context, default=str),
                )
                db.add(new_session)
                db.flush()

        # 2. Extract synthesized outputs
        final_answer = None
        if state.final_response:
            final_answer = state.final_response.main_answer
        elif "synthesis" in state.intermediate_results:
            final_answer = state.intermediate_results["synthesis"].get("main_answer")

        # 3. Create ExecutionRunRecord
        verif = state.verification_result
        verif_status = verif.overall_status.value if verif else "unverified"
        conf_level = verif.confidence.overall_confidence.value if verif else "uncertain"
        heuristic_score = verif.confidence.heuristic_score if verif else 0.5

        crop = state.request_understanding.get("crop_detected")
        location_name = state.request.location.place_name if state.request.location else None

        run_rec = ExecutionRunRecord(
            run_id=run_id,
            session_id=session_id,
            request_id=state.request.request_id,
            query_text=state.request.text_query,
            crop=crop,
            location_name=location_name,
            status="failed" if state.execution_errors else "completed",
            verification_status=verif_status,
            confidence_level=conf_level,
            heuristic_score=heuristic_score,
            total_latency_ms=state.trace.total_latency_ms,
            total_cost_usd=state.trace.total_estimated_cost_usd,
            total_tokens=sum(m.total_tokens for m in state.trace.model_calls),
            step_count=len(state.execution_plan.steps) if state.execution_plan else 0,
            final_answer=final_answer,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(run_rec)
        db.flush()

        # 4. Persist Plan Steps
        if state.execution_plan:
            for step in state.execution_plan.steps:
                step_rec = PlanStepRecord(
                    run_id=run_id,
                    step_id=step.step_id,
                    step_number=step.step_number,
                    title=step.title,
                    task_type=step.task_type.value,
                    assigned_model_id=step.assigned_model_id,
                    status=state.step_statuses.get(step.step_id, step.status).value,
                    latency_ms=step.actual_latency_ms or 0.0,
                    cost_usd=step.actual_cost_usd or 0.0,
                    dependencies_json=json.dumps(step.dependencies, default=str),
                    error_message=step.error_message,
                )
                db.add(step_rec)

        # 5. Persist Model Calls
        for call in state.trace.model_calls:
            model_rec = ModelCallRecord(
                run_id=run_id,
                step_id=call.step_id,
                model_id=call.model_id,
                provider=call.provider,
                prompt_tokens=call.prompt_tokens,
                completion_tokens=call.completion_tokens,
                total_tokens=call.total_tokens,
                estimated_cost_usd=call.estimated_cost_usd,
                latency_ms=call.latency_ms,
                is_mock=call.is_mock,
                created_at=call.timestamp,
            )
            db.add(model_rec)

        # 6. Persist Tool Invocations
        for step_id, tool_res in state.tool_results.items():
            tool_rec = ToolInvocationRecord(
                run_id=run_id,
                step_id=step_id,
                tool_name=tool_res.tool_name,
                status=tool_res.status.value,
                latency_ms=tool_res.latency_ms,
                is_mock=tool_res.is_mock,
                parameters_json=json.dumps(tool_res.structured_data or {}, default=str),
                raw_output_snippet=str(tool_res.raw_output)[:500] if tool_res.raw_output else None,
                created_at=tool_res.timestamp,
            )
            db.add(tool_rec)

        # 7. Persist Retrieved Evidence
        for ev in state.retrieved_evidence:
            ev_rec = EvidenceRecord(
                run_id=run_id,
                source_type=ev.source_type,
                source_name=ev.source_name,
                location_reference=ev.location_reference,
                content_snippet=ev.content_snippet,
                relevance_score=ev.relevance_score,
                created_at=ev.created_at,
            )
            db.add(ev_rec)

        # 8. Persist Verification Checks
        if verif:
            for check in verif.checks:
                check_rec = VerificationCheckRecord(
                    run_id=run_id,
                    check_type=check.check_type,
                    status=check.status.value,
                    target_claim=check.target_claim,
                    details=check.details,
                    deterministic_passed=check.deterministic_passed,
                )
                db.add(check_rec)

        # 9. Persist Recovery Events
        for event in state.recovery_events:
            rec_event = RecoveryEventRecord(
                run_id=run_id,
                step_id=event.step_id,
                trigger_reason=event.trigger_reason,
                action_taken=event.action_taken.value,
                from_target=event.from_target,
                to_target=event.to_target,
                success=event.success,
                details=event.details,
                created_at=event.timestamp,
            )
            db.add(rec_event)

        db.commit()
        db.refresh(run_rec)
        logger.info(f"Successfully persisted complete execution trace for run '{run_id}'.")
        return run_rec

    @staticmethod
    def get_run_trace(run_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """Retrieves complete trace details for a given execution run ID."""
        run = db.query(ExecutionRunRecord).filter_by(run_id=run_id).first()
        if not run:
            return None

        return {
            "run_id": run.run_id,
            "session_id": run.session_id,
            "request_id": run.request_id,
            "query_text": run.query_text,
            "crop": run.crop,
            "location_name": run.location_name,
            "status": run.status,
            "verification_status": run.verification_status,
            "confidence_level": run.confidence_level,
            "heuristic_score": run.heuristic_score,
            "total_latency_ms": run.total_latency_ms,
            "total_cost_usd": run.total_cost_usd,
            "total_tokens": run.total_tokens,
            "step_count": run.step_count,
            "final_answer": run.final_answer,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "steps": [
                {
                    "step_id": s.step_id,
                    "step_number": s.step_number,
                    "title": s.title,
                    "task_type": s.task_type,
                    "assigned_model_id": s.assigned_model_id,
                    "status": s.status,
                    "latency_ms": s.latency_ms,
                    "cost_usd": s.cost_usd,
                    "dependencies": json.loads(s.dependencies_json or "[]"),
                    "error_message": s.error_message,
                }
                for s in run.steps
            ],
            "model_calls": [
                {
                    "step_id": m.step_id,
                    "model_id": m.model_id,
                    "provider": m.provider,
                    "prompt_tokens": m.prompt_tokens,
                    "completion_tokens": m.completion_tokens,
                    "total_tokens": m.total_tokens,
                    "estimated_cost_usd": m.estimated_cost_usd,
                    "latency_ms": m.latency_ms,
                    "is_mock": m.is_mock,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in run.model_calls
            ],
            "tool_invocations": [
                {
                    "step_id": t.step_id,
                    "tool_name": t.tool_name,
                    "status": t.status,
                    "latency_ms": t.latency_ms,
                    "is_mock": t.is_mock,
                    "parameters": json.loads(t.parameters_json or "{}"),
                }
                for t in run.tool_invocations
            ],
            "evidence": [
                {
                    "source_type": e.source_type,
                    "source_name": e.source_name,
                    "location_reference": e.location_reference,
                    "content_snippet": e.content_snippet,
                    "relevance_score": e.relevance_score,
                }
                for e in run.evidence_items
            ],
            "verification_checks": [
                {
                    "check_type": v.check_type,
                    "status": v.status,
                    "target_claim": v.target_claim,
                    "details": v.details,
                    "deterministic_passed": v.deterministic_passed,
                }
                for v in run.verification_checks
            ],
            "recovery_events": [
                {
                    "step_id": r.step_id,
                    "trigger_reason": r.trigger_reason,
                    "action_taken": r.action_taken,
                    "from_target": r.from_target,
                    "to_target": r.to_target,
                    "success": r.success,
                    "details": r.details,
                }
                for r in run.recovery_events
            ],
        }

    @staticmethod
    def list_runs(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        crop: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Returns paginated summary list of execution runs."""
        query = db.query(ExecutionRunRecord)
        if crop:
            query = query.filter(ExecutionRunRecord.crop.ilike(f"%{crop}%"))
        if status:
            query = query.filter_by(status=status)

        runs = query.order_by(ExecutionRunRecord.created_at.desc()).offset(offset).limit(limit).all()
        return [
            {
                "run_id": r.run_id,
                "session_id": r.session_id,
                "request_id": r.request_id,
                "query_text": r.query_text,
                "crop": r.crop,
                "location_name": r.location_name,
                "status": r.status,
                "verification_status": r.verification_status,
                "confidence_level": r.confidence_level,
                "heuristic_score": r.heuristic_score,
                "total_latency_ms": r.total_latency_ms,
                "total_cost_usd": r.total_cost_usd,
                "step_count": r.step_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]

    @staticmethod
    def add_user_feedback(
        db: Session,
        run_id: str,
        rating: int,
        is_helpful: bool = True,
        comment: Optional[str] = None,
    ) -> UserFeedbackRecord:
        """Stores post-advisory user evaluation feedback."""
        feedback = UserFeedbackRecord(
            feedback_id=f"fb_{uuid4().hex[:12]}",
            run_id=run_id,
            rating=rating,
            is_helpful=is_helpful,
            comment=comment,
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
