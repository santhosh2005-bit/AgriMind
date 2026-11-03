"""File ingestion and multimodal upload API endpoints."""

import os
from pathlib import Path
from uuid import uuid4
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel

from backend.app.schemas.enums import InputModality
from backend.app.schemas.request import InputMetadata
from backend.app.processing.image_processor import default_image_processor
from backend.app.processing.pdf_processor import default_pdf_processor
from backend.app.processing.tabular_processor import default_tabular_processor
from backend.app.core.config import settings

logger = logging.getLogger("agrimind.api.ingestion")
router = APIRouter(prefix="/v1/upload", tags=["Multimodal Ingestion"])


class UploadResponse(BaseModel):
    metadata: InputMetadata
    processing_summary: Dict[str, Any]


@router.post("", response_model=UploadResponse)
async def upload_multimodal_file(file: UploadFile = File(...)):
    """
    Safely ingest and process uploaded crop photographs, PDF bulletins, or CSV/JSON records.
    Validates file sizes, calculates SHA256 checksums, and extracts empirical properties.
    """
    settings.ensure_directories()
    raw_filename = file.filename or "uploaded_file"
    ext = Path(raw_filename).suffix.lower()

    # Determine modality
    if ext in [".jpg", ".jpeg", ".png", ".webp"]:
        modality = InputModality.IMAGE
    elif ext == ".pdf":
        modality = InputModality.PDF
    elif ext == ".csv":
        modality = InputModality.CSV
    elif ext == ".json":
        modality = InputModality.JSON
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed: .jpg, .jpeg, .png, .webp, .pdf, .csv, .json"
        )

    content = await file.read()
    file_size = len(content)

    if file_size > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum permitted limit of 25MB."
        )

    # Save to upload dir with collision-resistant name
    safe_name = f"{uuid4().hex[:8]}_{Path(raw_filename).name}"
    save_path = Path(settings.UPLOAD_DIR) / safe_name
    save_path.write_bytes(content)

    processing_summary: Dict[str, Any] = {}
    extracted_summary_text: Optional[str] = None
    checksum: str = ""

    try:
        if modality == InputModality.IMAGE:
            img_result = default_image_processor.process_image(content, filename=raw_filename)
            checksum = img_result.checksum_sha256
            processing_summary = img_result.model_dump()
            extracted_summary_text = (
                f"Image {img_result.width}x{img_result.height}px. "
                f"Green canopy: {img_result.color_metrics.green_canopy_pct}%, "
                f"Chlorosis: {img_result.color_metrics.yellow_chlorosis_pct}%. "
                f"Blur score: {img_result.laplacian_blur_score}."
            )

        elif modality == InputModality.PDF:
            pdf_result = default_pdf_processor.process_pdf(content, filename=raw_filename)
            checksum = pdf_result.checksum_sha256
            processing_summary = pdf_result.model_dump()
            extracted_summary_text = (
                f"PDF with {pdf_result.total_pages} page(s) and {pdf_result.total_words} words. "
                f"Topics detected: {', '.join(pdf_result.detected_topics) or 'General Agronomy'}."
            )

        elif modality in [InputModality.CSV, InputModality.JSON]:
            tab_result = default_tabular_processor.process_tabular(content, filename=raw_filename)
            checksum = tab_result.checksum_sha256
            processing_summary = tab_result.model_dump()
            extracted_summary_text = (
                f"Tabular {tab_result.format} with {tab_result.summary.row_count} rows, {tab_result.summary.column_count} columns. "
                f"Mean pH: {tab_result.summary.average_soil_ph or 'N/A'}. Saline parcels: {tab_result.summary.saline_parcels_count or 0}."
            )

    except Exception as proc_err:
        logger.error(f"Error processing uploaded file '{raw_filename}': {str(proc_err)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File validation/processing error: {str(proc_err)}"
        )

    metadata = InputMetadata(
        modality=modality,
        filename=raw_filename,
        mime_type=file.content_type,
        file_size_bytes=file_size,
        storage_path=str(save_path),
        checksum_sha256=checksum,
        extracted_summary=extracted_summary_text,
        is_untrusted=True,
    )

    return UploadResponse(metadata=metadata, processing_summary=processing_summary)
