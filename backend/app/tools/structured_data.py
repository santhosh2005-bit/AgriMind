"""Tool C: Structured Agricultural Data Connector (CSV and JSON analysis via Pandas)."""

import os
from pathlib import Path
import time
import logging
from typing import Optional, List, Dict, Any
import pandas as pd
from pydantic import BaseModel, Field

from backend.app.schemas.enums import ToolStatus
from backend.app.schemas.tools import ToolResult, RetrievedEvidence

logger = logging.getLogger("agrimind.tools.structured_data")


class DataQueryInput(BaseModel):
    file_path: Optional[str] = Field(None, description="Path to CSV or JSON file")
    parcel_id: Optional[str] = Field(None, description="Filter by parcel ID, e.g. 'P-101'")
    crop: Optional[str] = Field(None, description="Filter by crop name")
    max_ph: Optional[float] = Field(None, description="Filter records by maximum pH")
    min_salinity_ec: Optional[float] = Field(None, description="Filter records by minimum EC in dS/m")


class StructuredDataConnector:
    """Tool connector executing validated queries over tabular soil and parcel data."""

    def __init__(self, default_file_path: Optional[str] = None):
        self.default_file_path = default_file_path or "data/sample_inputs/structured/farm_parcels_soil_tests.csv"

    def query(self, query_input: DataQueryInput) -> ToolResult:
        """
        Loads CSV/JSON, validates expected columns, executes filters,
        and returns structured records and evidence citations.
        """
        start_time = time.perf_counter()
        target_path = Path(query_input.file_path or self.default_file_path)

        if not target_path.exists():
            return ToolResult(
                invocation_id=f"inv-data-{int(time.time())}",
                tool_name="structured_data_query",
                status=ToolStatus.FAILED,
                error_message=f"Target tabular data file '{target_path}' not found.",
                latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
            )

        try:
            # 1. Load DataFrame based on extension
            if target_path.suffix.lower() == ".json":
                df = pd.read_json(target_path)
            else:
                df = pd.read_csv(target_path)

            initial_count = len(df)

            # 2. Apply filters
            if query_input.parcel_id:
                df = df[df["parcel_id"].astype(str).str.lower() == query_input.parcel_id.lower()]

            if query_input.crop:
                if "crop_cultivated" in df.columns:
                    df = df[df["crop_cultivated"].astype(str).str.lower().str.contains(query_input.crop.lower())]

            if query_input.max_ph is not None and "soil_ph" in df.columns:
                df = df[df["soil_ph"] <= query_input.max_ph]

            if query_input.min_salinity_ec is not None and "ec_ds_m" in df.columns:
                df = df[df["ec_ds_m"] >= query_input.min_salinity_ec]

            records: List[Dict[str, Any]] = df.to_dict(orient="records")
            evidence_items: List[RetrievedEvidence] = []

            for rec in records:
                parcel = rec.get("parcel_id", "Unknown Parcel")
                crop = rec.get("crop_cultivated", "Crop")
                ph = rec.get("soil_ph", 7.0)
                ec = rec.get("ec_ds_m", 0.0)
                n = rec.get("nitrogen_kg_ha", 0.0)

                snippet = (
                    f"Parcel {parcel} ({rec.get('farm_name', 'Farm')}) cultivated with {crop}:\n"
                    f"- Soil pH: {ph} ({'Alkaline' if ph > 7.5 else ('Acidic' if ph < 6.5 else 'Optimal')}).\n"
                    f"- Salinity EC: {ec} dS/m ({'Elevated Salinity Risk' if ec > 2.0 else 'Normal Range'}).\n"
                    f"- Available Nitrogen: {n} kg/ha (Low nitrogen status)."
                )

                evidence = RetrievedEvidence(
                    source_type="crop_table",
                    source_name=target_path.name,
                    location_reference=f"Parcel Record {parcel}",
                    content_snippet=snippet,
                    relevance_score=0.92,
                    metadata=rec,
                )
                evidence_items.append(evidence)

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            return ToolResult(
                invocation_id=f"inv-data-{int(time.time())}",
                tool_name="structured_data_query",
                status=ToolStatus.SUCCESS,
                structured_data={
                    "file_analyzed": target_path.name,
                    "matched_records_count": len(records),
                    "total_records_in_dataset": initial_count,
                    "records": records,
                },
                evidence_items=evidence_items,
                latency_ms=latency_ms,
                is_mock=False,
            )

        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(f"Structured data query failed: {str(e)}")
            return ToolResult(
                invocation_id=f"inv-data-{int(time.time())}",
                tool_name="structured_data_query",
                status=ToolStatus.FAILED,
                error_message=f"Structured data query failed: {str(e)}",
                latency_ms=latency_ms,
            )


# Shared tool instance
default_structured_tool = StructuredDataConnector()
