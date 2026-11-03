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


class ParcelIntelligence(BaseModel):
    """Cadastral parcel & geospatial context for land records."""
    survey_number: Optional[str] = Field(None, description="E.g. Survey No. 202/55 or 42")
    village: Optional[str] = Field(None, description="Village or Taluk name")
    district: Optional[str] = Field(None, description="District / State")
    latitude: float = Field(default=11.0168)
    longitude: float = Field(default=76.9558)
    area_acres: Optional[float] = Field(default=2.4)
    boundary_polygon: List[List[float]] = Field(
        default_factory=list,
        description="Coordinates [[lat, lon], ...] defining parcel boundary"
    )


class MandiMarketPrice(BaseModel):
    """Live APMC/Mandi commodity wholesale rates."""
    commodity: str = Field(..., description="Crop commodity name")
    market: str = Field(..., description="Mandi/APMC market yard")
    modal_price_rs_qtl: int = Field(..., description="Modal price in INR per Quintal")
    min_price: int
    max_price: int
    trend: str = Field(default="Stable", description="'Rising', 'Falling', 'Stable'")
    price_date: str


class ChemicalDilutionSpec(BaseModel):
    """Safe tank-mix and dosage specification."""
    chemical_name: str
    recommended_dosage_per_liter: str
    tank_sizes_liters: List[int] = Field(default_factory=lambda: [15, 100, 500])
    compatibility_warnings: List[str] = Field(default_factory=list)
    safe_water_ph_range: str = Field(default="6.0 - 7.0")


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

    # Advanced FarmwiseAI features
    parcel_intelligence: Optional[ParcelIntelligence] = Field(
        default=None,
        description="Cadastral map boundaries, survey numbers, and geo-coordinates"
    )
    mandi_prices: List[MandiMarketPrice] = Field(
        default_factory=list,
        description="Current agricultural market prices (APMC/Mandi rates)"
    )
    chemical_calculator: Optional[ChemicalDilutionSpec] = Field(
        default=None,
        description="Interactive tank-mix dilution calculator and compatibility specifications"
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
