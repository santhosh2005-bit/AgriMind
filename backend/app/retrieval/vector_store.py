"""Vector store management using FAISS and dense sentence embeddings."""

import os
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss

from backend.app.schemas.tools import RetrievedEvidence
from backend.app.core.config import settings

logger = logging.getLogger("agrimind.retrieval.faiss")


class DocumentChunk:
    """A granular chunk of agricultural knowledge with section citation."""

    def __init__(
        self,
        chunk_id: str,
        document_name: str,
        section_title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.chunk_id = chunk_id
        self.document_name = document_name
        self.section_title = section_title
        self.content = content
        self.metadata = metadata or {}


class FAISSKnowledgeIndex:
    """
    Manages embedding generation, vector indexing, persistence, and semantic retrieval
    over agricultural extension bulletins and advisories.
    """

    def __init__(
        self,
        index_dir: Optional[str] = None,
        model_name: Optional[str] = None,
        embedding_dim: int = 384,
    ):
        self.index_dir = Path(index_dir or settings.FAISS_INDEX_PATH)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.embedding_dim = embedding_dim

        self.index: Optional[faiss.Index] = None
        self.chunks: List[DocumentChunk] = []
        self._embedder = None
        self._embedder_initialized = False

    def _init_embedder(self):
        """Initializes sentence-transformers embedding model."""
        if not self._embedder_initialized:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(self.model_name)
                self.embedding_dim = self._embedder.get_sentence_embedding_dimension()
                self._embedder_initialized = True
                logger.info(f"Loaded SentenceTransformer '{self.model_name}' (dim={self.embedding_dim})")
            except Exception as e:
                logger.warning(
                    f"Could not load SentenceTransformer '{self.model_name}' ({str(e)}). "
                    f"Falling back to deterministic hashed vector representation."
                )
                self._embedder = None
                self._embedder_initialized = True

    def compute_embedding(self, text: str) -> np.ndarray:
        """Computes a normalized dense vector embedding for a piece of text."""
        self._init_embedder()

        if self._embedder is not None:
            emb = self._embedder.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            return emb.astype(np.float32)

        # Robust deterministic fallback vector using character trigram hashing
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        words = text.lower().split()
        for i, word in enumerate(words):
            h = hash(word) % self.embedding_dim
            vec[h] += 1.0 / (1.0 + (i * 0.05))
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def build_from_directory(self, knowledge_dir: Optional[str] = None) -> int:
        """
        Parses all Markdown and PDF files in the knowledge directory,
        splits into section chunks, computes vectors, and builds the FAISS index.
        """
        target_dir = Path(knowledge_dir or settings.KNOWLEDGE_DIR)
        if not target_dir.exists():
            logger.warning(f"Knowledge directory '{target_dir}' does not exist.")
            return 0

        self.chunks = []
        logger.info(f"Ingesting agricultural advisories from {target_dir}...")

        # 1. Parse Markdown advisories
        for md_file in target_dir.glob("*.md"):
            self._ingest_markdown_file(md_file)

        # 2. Parse PDF advisories (using PyMuPDF)
        for pdf_file in target_dir.glob("*.pdf"):
            self._ingest_pdf_file(pdf_file)

        if not self.chunks:
            logger.warning("No knowledge documents found to index.")
            return 0

        # 3. Compute embeddings
        logger.info(f"Computing embeddings for {len(self.chunks)} knowledge chunks...")
        embeddings = []
        for chunk in self.chunks:
            vec = self.compute_embedding(f"{chunk.section_title}\n{chunk.content}")
            embeddings.append(vec)

        matrix = np.vstack(embeddings).astype(np.float32)

        # 4. Create and populate FAISS Inner Product (Cosine similarity) index
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.index.add(matrix)

        logger.info(f"Successfully built FAISS index with {self.index.ntotal} vectors.")
        return len(self.chunks)

    def _ingest_markdown_file(self, file_path: Path):
        try:
            content = file_path.read_text(encoding="utf-8")
            sections = content.split("\n## ")
            doc_name = file_path.name

            for i, sec in enumerate(sections):
                lines = sec.strip().split("\n")
                if not lines:
                    continue
                header = lines[0].replace("#", "").strip()
                body = "\n".join(lines[1:]).strip()
                if len(body) > 30:
                    chunk = DocumentChunk(
                        chunk_id=f"{doc_name}-sec{i}",
                        document_name=doc_name,
                        section_title=f"Section: {header}",
                        content=body,
                    )
                    self.chunks.append(chunk)
        except Exception as e:
            logger.error(f"Error parsing markdown file '{file_path}': {str(e)}")

    def _ingest_pdf_file(self, file_path: Path):
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(file_path))
            doc_name = file_path.name
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text().strip()
                if len(text) > 40:
                    chunk = DocumentChunk(
                        chunk_id=f"{doc_name}-p{page_num + 1}",
                        document_name=doc_name,
                        section_title=f"Page {page_num + 1}",
                        content=text,
                    )
                    self.chunks.append(chunk)
        except Exception as e:
            logger.error(f"Error extracting PDF file '{file_path}': {str(e)}")

    def search(self, query: str, top_k: int = 3) -> List[RetrievedEvidence]:
        """
        Executes semantic search against the FAISS vector index,
        returning top-k structured RetrievedEvidence objects with section pointers.
        """
        if self.index is None or not self.chunks:
            self.build_from_directory()

        if self.index is None or self.index.ntotal == 0:
            logger.warning("FAISS index is empty; returning empty evidence.")
            return []

        q_vec = self.compute_embedding(query).reshape(1, -1)
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(q_vec, k)

        evidence_items: List[RetrievedEvidence] = []
        for sim, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx]
            relevance = float(max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 1.0 else sim)))

            ev = RetrievedEvidence(
                source_type="advisory_bulletin",
                source_name=chunk.document_name,
                location_reference=chunk.section_title,
                content_snippet=chunk.content[:400] + ("..." if len(chunk.content) > 400 else ""),
                relevance_score=round(relevance, 3),
                metadata={"full_length": len(chunk.content), "chunk_id": chunk.chunk_id},
            )
            evidence_items.append(ev)

        return evidence_items


# Global FAISS knowledge index instance
default_knowledge_index = FAISSKnowledgeIndex()
