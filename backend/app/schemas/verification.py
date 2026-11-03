"""Schemas for output verification, factual consistency checks, and confidence rating."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field
from backend.app.schemas.enums import VerificationStatus, ConfidenceLevel


class VerificationCheck(BaseModel):
    """An individual verification check performed on intermediate or final output."""
    check_id: str = Field(default_factory=lambda: str(uuid4()))
    check_type: str = Field(
        ...,
        description="Type of check: 'schema_validity', 'deterministic_calculation', 'evidence_grounding', 'contradiction_check', 'bounds_check'"
    )
    status: VerificationStatus = Field(...)
    details: str = Field(..., description="Explanation of what was checked and the finding")
    target_claim: Optional[str] = Field(None, description="The specific factual claim or field tested")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="IDs of evidence verifying this claim")
    deterministic_passed: Optional[bool] = Field(
        None,
        description="True if calculation was verified with deterministic Python code"
    )


class ConfidenceBreakdown(BaseModel):
    """Transparent multidimensional confidence assessment (not uncalibrated LLM confidence)."""
    evidence_coverage_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Proportion of claims supported by evidence")
    schema_validity_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Strictness of Pydantic parsing")
    data_completeness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Presence of all required inputs/tools")
    overall_confidence: ConfidenceLevel = Field(default=ConfidenceLevel.UNCERTAIN)
    heuristic_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Heuristic composite score")
    formula_explanation: str = Field(
        default="heuristic = 0.4*evidence_coverage + 0.3*data_completeness + 0.3*verification_checks",
        description="Documentation of formula as required by specification"
    )


class VerificationResult(BaseModel):
    """Overall outcome of the verification and critic stage."""
    verification_id: str = Field(default_factory=lambda: str(uuid4()))
    overall_status: VerificationStatus = Field(default=VerificationStatus.NEEDS_REVIEW)
    checks: List[VerificationCheck] = Field(default_factory=list)
    confidence: ConfidenceBreakdown = Field(default_factory=ConfidenceBreakdown)
    missing_information: List[str] = Field(default_factory=list, description="Information gaps that prevent definitive diagnosis")
    conflicts_detected: List[str] = Field(default_factory=list, description="Direct contradictions between sources or models")
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.status == VerificationStatus.PASSED)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checks if c.status == VerificationStatus.FAILED)
