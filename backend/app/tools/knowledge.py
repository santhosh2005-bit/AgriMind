"""Tool B: Agricultural Knowledge Retrieval Connector using FAISS."""

import time
import logging
from typing import Optional, List
from pydantic import BaseModel, Field

from backend.app.schemas.enums import ToolStatus
from backend.app.schemas.tools import ToolResult, RetrievedEvidence
from backend.app.retrieval.vector_store import default_knowledge_index

logger = logging.getLogger("agrimind.tools.knowledge")


class KnowledgeQueryInput(BaseModel):
    query: str = Field(..., description="Agricultural symptom, disease, or pest query")
    crop_filter: Optional[str] = Field(None, description="Optional crop filter, e.g. 'tomato' or 'wheat'")
    top_k: int = Field(default=3, ge=1, le=10)


class KnowledgeRetrieverTool:
    """Tool connector executing grounded semantic retrieval across indexed agronomic advisories."""

    def __init__(self, index=None):
        self.index = index or default_knowledge_index

    def retrieve(self, query_input: KnowledgeQueryInput) -> ToolResult:
        """
        Executes semantic search against the FAISS index and returns structured evidence.
        """
        start_time = time.perf_counter()
        search_query = query_input.query
        if query_input.crop_filter:
            search_query = f"{query_input.crop_filter} {search_query}"

        try:
            evidence_items = self.index.search(query=search_query, top_k=query_input.top_k)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            structured_summary = {
                "query": query_input.query,
                "matches_found": len(evidence_items),
                "top_sources": list({e.source_name for e in evidence_items}),
            }

            return ToolResult(
                invocation_id=f"inv-rag-{int(time.time())}",
                tool_name="agricultural_retriever",
                status=ToolStatus.SUCCESS if evidence_items else ToolStatus.SKIPPED,
                structured_data=structured_summary,
                evidence_items=evidence_items,
                latency_ms=latency_ms,
                is_mock=False,
            )

        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(f"Knowledge retrieval failed: {str(e)}")
            return ToolResult(
                invocation_id=f"inv-rag-{int(time.time())}",
                tool_name="agricultural_retriever",
                status=ToolStatus.FAILED,
                error_message=f"Agricultural knowledge retrieval failed: {str(e)}",
                latency_ms=latency_ms,
            )


# Shared tool instance
default_knowledge_tool = KnowledgeRetrieverTool()
