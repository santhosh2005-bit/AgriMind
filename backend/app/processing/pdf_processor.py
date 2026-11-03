"""PDF document processing pipeline using PyMuPDF (fitz) and Tesseract OCR."""

import hashlib
import io
import re
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger("agrimind.processing.pdf")

MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_PAGE_COUNT = 100


class PDFPageText(BaseModel):
    page_number: int
    char_count: int
    word_count: int
    text_content: str
    section_headings: List[str] = Field(default_factory=list)
    is_ocr_fallback: bool = False


class ProcessedPDFResult(BaseModel):
    filename: str
    total_pages: int
    total_words: int
    checksum_sha256: str
    pages: List[PDFPageText] = Field(default_factory=list)
    detected_topics: List[str] = Field(default_factory=list)
    untrusted_sanitized: bool = True
    has_scanned_pages: bool = False


class PDFProcessor:
    """Extracts, structures, and sanitizes text from agricultural advisory PDFs."""

    def __init__(self, ocr_word_threshold: int = 30):
        self.ocr_word_threshold = ocr_word_threshold

    def sanitize_untrusted_text(self, text: str) -> str:
        """
        Sanitizes extracted document text to prevent prompt injection attempts
        embedded within untrusted user-supplied documents.
        """
        # Neutralize system override instructions
        patterns = [
            r"(?i)ignore\s+(all\s+)?previous\s+instructions",
            r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
            r"(?i)system\s*:\s*",
            r"(?i)admin\s+override\s*:\s*",
        ]
        sanitized = text
        for p in patterns:
            sanitized = re.sub(p, "[REDACTED_UNTRUSTED_INSTRUCTION]", sanitized)
        return sanitized

    def process_pdf(self, pdf_bytes: bytes, filename: str = "document.pdf") -> ProcessedPDFResult:
        """
        Extracts text from PDF page-by-page using PyMuPDF.
        Falls back to OCR if page text is inadequate or scanned.
        """
        if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
            raise ValueError(f"PDF size ({len(pdf_bytes) / (1024*1024):.1f}MB) exceeds 25MB limit.")

        sha256 = hashlib.sha256(pdf_bytes).hexdigest()

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Failed to parse PDF document: {str(e)}") from e

        total_pages = len(doc)
        if total_pages > MAX_PAGE_COUNT:
            doc.close()
            raise ValueError(f"PDF has {total_pages} pages, which exceeds maximum limit of {MAX_PAGE_COUNT} pages.")

        pages_result: List[PDFPageText] = []
        has_scanned = False
        all_text_for_topics = []

        for page_idx in range(total_pages):
            page = doc.load_page(page_idx)
            raw_text = page.get_text("text").strip()
            word_count = len(raw_text.split())
            is_ocr = False

            # Check if page is scanned or text extraction is inadequate
            if word_count < self.ocr_word_threshold:
                try:
                    import pytesseract
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(img).strip()
                    if len(ocr_text.split()) > word_count:
                        raw_text = ocr_text
                        word_count = len(raw_text.split())
                        is_ocr = True
                        has_scanned = True
                except Exception as ocr_err:
                    logger.debug(f"OCR fallback skipped on page {page_idx + 1}: {str(ocr_err)}")

            sanitized_text = self.sanitize_untrusted_text(raw_text)

            # Extract simple section headings (lines starting with bold, capital, or numbers)
            headings: List[str] = []
            for line in sanitized_text.split("\n"):
                line_clean = line.strip()
                if (line_clean.isupper() and 3 < len(line_clean) < 50) or line_clean.startswith(("#", "Section", "Chapter")):
                    headings.append(line_clean.lstrip("#").strip())

            page_data = PDFPageText(
                page_number=page_idx + 1,
                char_count=len(sanitized_text),
                word_count=word_count,
                text_content=sanitized_text,
                section_headings=headings[:5],
                is_ocr_fallback=is_ocr,
            )
            pages_result.append(page_data)
            all_text_for_topics.append(sanitized_text)

        doc.close()

        # Extract topics mentioned
        combined_text = " ".join(all_text_for_topics).lower()
        topic_keywords = [
            "pest management", "irrigation", "fertilizer", "yellow leaf curl",
            "whitefly", "fungicide", "nitrogen", "soil ph", "salinity"
        ]
        detected_topics = [t for t in topic_keywords if t in combined_text]

        total_words = sum(p.word_count for p in pages_result)

        return ProcessedPDFResult(
            filename=filename,
            total_pages=total_pages,
            total_words=total_words,
            checksum_sha256=sha256,
            pages=pages_result,
            detected_topics=detected_topics,
            has_scanned_pages=has_scanned,
        )


default_pdf_processor = PDFProcessor()
