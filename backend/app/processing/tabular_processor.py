"""Tabular data processing pipeline for CSV and JSON soil/parcel records."""

import hashlib
import io
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import pandas as pd

logger = logging.getLogger("agrimind.processing.tabular")

MAX_TABULAR_ROWS = 50000


class TabularSummary(BaseModel):
    row_count: int
    column_count: int
    columns: List[str]
    detected_crop_types: List[str] = Field(default_factory=list)
    average_soil_ph: Optional[float] = None
    saline_parcels_count: Optional[int] = None
    records_sample: List[Dict[str, Any]] = Field(default_factory=list)


class ProcessedTabularResult(BaseModel):
    filename: str
    format: str  # "CSV" or "JSON"
    checksum_sha256: str
    summary: TabularSummary
    validated: bool = True
    diagnostic_insights: List[str] = Field(default_factory=list)


class TabularProcessor:
    """Parses, validates, and analyzes tabular agricultural datasets."""

    def process_tabular(
        self, data_bytes: bytes, filename: str = "data.csv"
    ) -> ProcessedTabularResult:
        """
        Parses CSV/JSON data into DataFrame, validates agricultural schema,
        and extracts soil and crop statistical summaries.
        """
        sha256 = hashlib.sha256(data_bytes).hexdigest()
        is_json = filename.lower().endswith(".json")

        try:
            if is_json:
                df = pd.read_json(io.BytesIO(data_bytes))
            else:
                df = pd.read_csv(io.BytesIO(data_bytes))
        except Exception as e:
            raise ValueError(f"Failed to parse tabular data from '{filename}': {str(e)}") from e

        if len(df) > MAX_TABULAR_ROWS:
            raise ValueError(f"Dataset has {len(df)} rows, exceeding maximum limit of {MAX_TABULAR_ROWS} rows.")

        columns = [str(c).strip() for c in df.columns]
        row_count = len(df)
        cols_lower = [c.lower() for c in columns]

        # 1. Detect crops
        crops = []
        for col_name in ["crop", "crop_cultivated", "crop_name", "commodity"]:
            if col_name in cols_lower:
                actual_col = columns[cols_lower.index(col_name)]
                crops = [str(x) for x in df[actual_col].dropna().unique().tolist()]
                break

        # 2. Compute soil statistics if soil columns present
        avg_ph = None
        saline_count = None
        insights = []

        for col_name in ["soil_ph", "ph"]:
            if col_name in cols_lower:
                actual_col = columns[cols_lower.index(col_name)]
                avg_ph = round(float(df[actual_col].mean()), 2)
                if avg_ph > 7.5:
                    insights.append(f"Mean soil pH is alkaline ({avg_ph}); micronutrient availability (Zn, Fe, Mn) may be restricted.")
                elif avg_ph < 6.0:
                    insights.append(f"Mean soil pH is acidic ({avg_ph}); liming may be recommended.")
                break

        for col_name in ["ec_ds_m", "ec", "salinity"]:
            if col_name in cols_lower:
                actual_col = columns[cols_lower.index(col_name)]
                saline_parcels = df[df[actual_col] >= 2.0]
                saline_count = len(saline_parcels)
                if saline_count > 0:
                    insights.append(f"{saline_count} parcel(s) exhibit elevated electrical conductivity (EC >= 2.0 dS/m), indicating salinity stress.")
                break

        summary = TabularSummary(
            row_count=row_count,
            column_count=len(columns),
            columns=columns,
            detected_crop_types=crops[:10],
            average_soil_ph=avg_ph,
            saline_parcels_count=saline_count,
            records_sample=df.head(5).to_dict(orient="records"),
        )

        return ProcessedTabularResult(
            filename=filename,
            format="JSON" if is_json else "CSV",
            checksum_sha256=sha256,
            summary=summary,
            diagnostic_insights=insights,
        )


default_tabular_processor = TabularProcessor()
