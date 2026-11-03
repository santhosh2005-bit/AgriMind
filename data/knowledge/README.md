# Knowledge Base Directory

Place agricultural advisory PDFs, bulletins, guidelines, and manuals in this directory.

Supported files:
- PDF advisory documents (e.g., ICAR pest management guidelines, university extension sheets).
- Markdown and text agricultural advisories.

The AgriMind FAISS ingestion pipeline will:
1. Extract text and page boundaries using PyMuPDF.
2. Fall back to OCR if scanned/image-only.
3. Chunk content with section preservation.
4. Generate embeddings via `sentence-transformers`.
5. Build and save a FAISS vector index under `data/knowledge/faiss_index/`.
