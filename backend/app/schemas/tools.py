"""Schemas for tool invocations, structured results, and retrieved evidence."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field
from backend.app.schemas.enums import ToolStatus


class RetrievedEvidence(BaseModel):
    """Structured evidence item extracted from documents, databases, or API results."""
    evidence_id: str = Field(default_factory=lambda: str(uuid4()))
    source_type: str = Field(..., description="E.g., 'advisory_pdf', 'weather_api', 'crop_table'")
    source_name: str = Field(..., description="Document filename, table name, or service identifier")
    location_reference: Optional[str] = Field(None, description="Page number, section header, or row ID")
    content_snippet: str = Field(..., min_length=1, description="Extracted factual excerpt or summary")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Vector similarity or retrieval score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context or timestamps")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolInvocation(BaseModel):
    """Specification of a tool request about to be executed."""
    invocation_id: str = Field(default_factory=lambda: str(uuid4()))
    step_id: str = Field(..., description="Plan step initiating this tool call")
    tool_name: str = Field(..., description="Registered tool identifier, e.g. 'weather_connector'")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Typed invocation arguments")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolResult(BaseModel):
    """Validated output from a completed or failed tool invocation."""
    invocation_id: str = Field(..., description="Matches the ToolInvocation ID")
    tool_name: str = Field(...)
    status: ToolStatus = Field(...)
    raw_output: Optional[Any] = Field(None, description="Raw unparsed output from tool")
    structured_data: Optional[Dict[str, Any]] = Field(None, description="Clean validated structured data")
    evidence_items: List[RetrievedEvidence] = Field(default_factory=list, description="Extracted evidence pieces")
    latency_ms: float = Field(default=0.0, ge=0)
    error_message: Optional[str] = None
    is_mock: bool = Field(default=False, description="Flag indicating if mock fixture was used")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
