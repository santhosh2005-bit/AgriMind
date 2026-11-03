"""Schemas for incoming user requests and attached multimodal metadata."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from backend.app.schemas.enums import InputModality, SupportedLanguage


class InputMetadata(BaseModel):
    """Metadata describing an uploaded or attached file/input."""
    input_id: str = Field(default_factory=lambda: str(uuid4()))
    modality: InputModality = Field(..., description="Modality of the attached input")
    filename: Optional[str] = Field(None, description="Original filename if uploaded")
    mime_type: Optional[str] = Field(None, description="MIME type of the asset")
    file_size_bytes: Optional[int] = Field(None, ge=0, description="Size in bytes")
    storage_path: Optional[str] = Field(None, description="Local or internal storage path")
    checksum_sha256: Optional[str] = Field(None, description="SHA256 checksum for integrity")
    extracted_summary: Optional[str] = Field(None, description="Initial summary or extracted metadata")
    is_untrusted: bool = Field(default=True, description="Flag indicating content must be treated as untrusted")


class LocationContext(BaseModel):
    """Geographic context for agricultural inquiries (e.g. weather, regional guidance)."""
    place_name: Optional[str] = Field(None, description="City, district, or region name")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude coordinate")
    elevation_meters: Optional[float] = Field(None, description="Elevation in meters if known")


class UserRequest(BaseModel):
    """Structured representation of the incoming agricultural inquiry."""
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique ID for this request")
    session_id: Optional[str] = Field(None, description="Session identifier for multi-turn tracking")
    text_query: str = Field(..., min_length=1, description="Primary natural language inquiry from the user")
    location: Optional[LocationContext] = Field(None, description="Location context for weather/regional lookups")
    inputs: List[InputMetadata] = Field(default_factory=list, description="Attached multimodal inputs")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="User or system constraints (e.g. timeout)")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="Optional farming profile (soil, crop history)")
    target_language: SupportedLanguage = Field(default=SupportedLanguage.AUTO, description="Desired delivery language")
    detected_language: Optional[SupportedLanguage] = Field(None, description="Automatically detected input language")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("text_query")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("text_query cannot be blank or only whitespace")
        return trimmed

    def get_modalities(self) -> List[InputModality]:
        """Return list of distinct modalities present in the request."""
        mods = {InputModality.TEXT}
        for inp in self.inputs:
            mods.add(inp.modality)
        return list(mods)
