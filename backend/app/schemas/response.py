"""Schemas for final structured response produced by AgriMind."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field
from backend.app.schemas.enums import VerificationStatus, SupportedLanguage
from backend.app.schemas.tools import RetrievedEvidence
from backend.app.schemas.verification import ConfidenceBreakdown


class SourceReference(BaseModel):
    """Specific citation linking recommendations or claims to source material."""
    reference_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(..., description="Document title or service name")
    location_pointer: Optional[str] = Field(None, description="Page number, table, or section identifier")
    citation_text: str = Field(..., description="Quote or factual reference")
    uri_or_path: Optional[str] = Field(None, description="File path or URL if applicable")


class VisualizationData(BaseModel):
    """Data-driven visualization payload conforming to Section 11 of requirements."""
    chart_type: str = Field(..., description="'weather_trend' | 'soil_metrics' | 'crop_comparison'")
    title: str = Field(..., description="Title of visualization")
    subtitle: Optional[str] = Field(None, description="Subtitle or geographical scope")
    data_source: str = Field(..., description="Explicit attribution of source data (e.g. Open-Meteo, Soil Lab CSV)")
    unit: Optional[str] = Field(None, description="Measurement units (°C, %, pH, dS/m)")
    labels: List[str] = Field(default_factory=list, description="X-axis category labels or timestamps")
    series: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Data series, e.g. [{'name': 'Max Temp (°C)', 'data': [32.1, 33.4], 'color': '#f97316'}]"
    )
    notes: Optional[str] = Field(None, description="Agronomic interpretation notes or threshold indicators")


class FinalResponse(BaseModel):
    """
    Standardized, structured output conforming to Section 9 of problem requirements.
    Distinguishes observed facts, retrieved evidence, possible causes, recommendations, and uncertainties.
    """
    response_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str = Field(..., description="Associated user request ID")
    request_summary: str = Field(..., min_length=5, description="Concise synopsis of the user's inquiry")
    main_answer: str = Field(..., min_length=10, description="Primary synthesized response")

    # Clear distinction of factual categories
    observed_facts: List[str] = Field(
        default_factory=list,
        description="Empirical observations extracted directly from user inputs (images, CSVs, text)"
    )
    retrieved_evidence: List[RetrievedEvidence] = Field(
        default_factory=list,
        description="Structured facts retrieved from advisory documents, weather APIs, or local databases"
    )
    possible_causes: List[str] = Field(
        default_factory=list,
        description="Plausible agronomic explanations for symptoms, explicitly labeled as non-definitive"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Evidence-backed next steps, cultural practices, or advisory consultations"
    )
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Actionable follow-up inquiries to narrow diagnosis or assist decision-making"
    )
    visualizations: List[VisualizationData] = Field(
        default_factory=list,
        description="Data-driven charts and structured representations derived from real tool telemetry"
    )
    uncertainties_and_limitations: List[str] = Field(
        default_factory=list,
        description="Explicit caveats regarding missing data, resolution limits, or model boundaries"
    )
    source_references: List[SourceReference] = Field(
        default_factory=list,
        description="Traceable citations to documents, sensors, or datasets"
    )
    language: SupportedLanguage = Field(
        default=SupportedLanguage.ENGLISH,
        description="Language of delivered response"
    )

    # Verification & Quality Indicators
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.PASSED,
        description="Verdict from the independent verification stage"
    )
    confidence_indicators: ConfidenceBreakdown = Field(
        default_factory=ConfidenceBreakdown,
        description="Multi-metric confidence and heuristic assessment"
    )

    # Telemetry and Execution reference
    trace_id: str = Field(..., description="Foreign key linking to detailed execution trace")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
