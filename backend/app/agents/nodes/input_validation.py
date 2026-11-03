"""Node 1: Input Validation and Safe Ingestion."""

import logging
from backend.app.schemas.enums import InputModality
from backend.app.agents.state import AgriMindState

logger = logging.getLogger("agrimind.node.input_validation")


def input_validation_node(state: AgriMindState) -> AgriMindState:
    """
    Validates user query, checks multimodal inputs, marks content untrusted,
    and initializes execution trace.
    """
    logger.info(f"Executing Input Validation for request '{state.request.request_id}'")

    # 1. Validate non-empty query
    query = state.request.text_query.strip()
    if not query:
        state.execution_errors.append("Validation Error: text_query cannot be empty.")
        return state

    # 2. Discover modalities
    detected = state.request.get_modalities()
    state.detected_modalities = detected

    # 3. Sanitize and enforce file safety
    MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit
    for inp in state.request.inputs:
        inp.is_untrusted = True  # Untrusted input constraint
        if inp.file_size_bytes and inp.file_size_bytes > MAX_FILE_SIZE_BYTES:
            state.execution_errors.append(
                f"File '{inp.filename}' exceeds maximum allowed size of 25MB."
            )

    # 4. Initialize trace
    state.trace.request_id = state.request.request_id
    state.execution_budget_seconds = state.request.constraints.get("budget_seconds", 120)

    logger.info(f"Input validation passed. Detected modalities: {[m.value for m in detected]}")
    return state
