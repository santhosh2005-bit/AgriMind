"""Image processing pipeline using Pillow and OpenCV for agricultural foliar diagnostics."""

import hashlib
import io
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from pydantic import BaseModel, Field
from PIL import Image, ImageOps
import cv2
import numpy as np

logger = logging.getLogger("agrimind.processing.image")

ALLOWED_IMAGE_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}
MAX_IMAGE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit


class ImageColorMetrics(BaseModel):
    mean_rgb: Tuple[float, float, float]
    green_canopy_pct: float = Field(..., description="Percentage of pixels in healthy green spectrum")
    yellow_chlorosis_pct: float = Field(..., description="Percentage of pixels in chlorotic yellow spectrum")
    brown_necrosis_pct: float = Field(..., description="Percentage of pixels in necrotic brown spectrum")
    chlorosis_severity_ratio: float = Field(..., description="Ratio of yellow chlorosis to green foliage")


class ProcessedImageResult(BaseModel):
    filename: str
    format: str
    width: int
    height: int
    aspect_ratio: float
    file_size_bytes: int
    checksum_sha256: str
    is_blurry: bool
    laplacian_blur_score: float
    color_metrics: ImageColorMetrics
    diagnostic_notes: List[str] = Field(default_factory=list)
    untrusted_sanitized: bool = True
    caveat: str = (
        "Visual processing extracts empirical color and texture properties. "
        "Photographic analysis alone cannot definitively confirm viral or bacterial pathology without lab assays."
    )


class ImageProcessor:
    """Validates, inspects, and analyzes foliar crop photographs."""

    def __init__(self, blur_threshold: float = 65.0):
        self.blur_threshold = blur_threshold

    def process_image(self, image_bytes: bytes, filename: str = "crop_image.jpg") -> ProcessedImageResult:
        """
        Validates image format and size, extracts metadata,
        and computes HSV foliar color distributions using OpenCV.
        """
        file_size = len(image_bytes)
        if file_size > MAX_IMAGE_SIZE_BYTES:
            raise ValueError(f"Image file size ({file_size / (1024*1024):.1f}MB) exceeds 15MB limit.")

        sha256 = hashlib.sha256(image_bytes).hexdigest()

        # 1. Pillow Inspection
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            pil_img = ImageOps.exif_transpose(pil_img)  # Correct orientation if EXIF present
            img_format = (pil_img.format or "JPEG").upper()
            if img_format not in ALLOWED_IMAGE_FORMATS and not filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                raise ValueError(f"Unsupported image format '{img_format}'. Allowed: {ALLOWED_IMAGE_FORMATS}")

            width, height = pil_img.size
            aspect_ratio = round(width / float(height), 2)

            # Ensure RGB
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")

        except Exception as e:
            raise ValueError(f"Corrupted or invalid image data: {str(e)}") from e

        # 2. OpenCV Agronomic Feature Extraction
        np_arr = np.frombuffer(image_bytes, np.uint8)
        cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if cv_img is None:
            # Fallback array conversion from PIL
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        # Blurriness check via Laplacian variance
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = laplacian_var < self.blur_threshold

        # Color Space Analysis (HSV)
        hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
        total_pixels = float(width * height)

        # Green foliage mask: H: 35-85, S: 40-255, V: 40-255
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        green_pixels = float(cv2.countNonZero(green_mask))
        green_pct = round((green_pixels / total_pixels) * 100.0, 1)

        # Yellow chlorosis mask: H: 18-35, S: 50-255, V: 50-255
        lower_yellow = np.array([18, 50, 50])
        upper_yellow = np.array([35, 255, 255])
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        yellow_pixels = float(cv2.countNonZero(yellow_mask))
        yellow_pct = round((yellow_pixels / total_pixels) * 100.0, 1)

        # Brown necrosis mask: H: 5-18, S: 50-200, V: 30-150
        lower_brown = np.array([5, 50, 30])
        upper_brown = np.array([18, 200, 150])
        brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)
        brown_pixels = float(cv2.countNonZero(brown_mask))
        brown_pct = round((brown_pixels / total_pixels) * 100.0, 1)

        # Chlorosis severity ratio
        chlorosis_ratio = round(yellow_pct / max(1.0, green_pct), 3)

        # Mean RGB
        mean_bgr = cv2.mean(cv_img)[:3]
        mean_rgb = (round(mean_bgr[2], 1), round(mean_bgr[1], 1), round(mean_bgr[0], 1))

        # Diagnostic notes based on extracted parameters
        notes: List[str] = []
        if is_blurry:
            notes.append(f"Image blur score ({laplacian_var:.1f}) is below clarity threshold ({self.blur_threshold}). Macro details may be obscured.")
        if yellow_pct > 15.0:
            notes.append(f"Elevated yellow foliar pigmentation detected ({yellow_pct}% of area), indicating interveinal chlorosis or leaf senescence.")
        if brown_pct > 8.0:
            notes.append(f"Necrotic lesions detected ({brown_pct}% of area), suggesting tissue death or blight progression.")
        if green_pct > 40.0:
            notes.append(f"Substantial viable green canopy retained ({green_pct}% of area).")

        color_metrics = ImageColorMetrics(
            mean_rgb=mean_rgb,
            green_canopy_pct=green_pct,
            yellow_chlorosis_pct=yellow_pct,
            brown_necrosis_pct=brown_pct,
            chlorosis_severity_ratio=chlorosis_ratio,
        )

        return ProcessedImageResult(
            filename=filename,
            format=img_format,
            width=width,
            height=height,
            aspect_ratio=aspect_ratio,
            file_size_bytes=file_size,
            checksum_sha256=sha256,
            is_blurry=is_blurry,
            laplacian_blur_score=round(laplacian_var, 2),
            color_metrics=color_metrics,
            diagnostic_notes=notes,
        )


default_image_processor = ImageProcessor()
