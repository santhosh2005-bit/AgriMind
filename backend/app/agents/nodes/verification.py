"""Node 7: Verification and Critic Node validating facts, calculations, and boundaries."""

import logging
from backend.app.schemas.enums import VerificationStatus
from backend.app.schemas.verification import VerificationResult
from backend.app.agents.state import AgriMindState
from backend.app.verification.critic import VerificationCritic

logger = logging.getLogger("agrimind.node.verification")


def verification_node(state: AgriMindState) -> AgriMindState:
    """
    Executes independent verification stage using VerificationCritic:
    1. Schema & 5-tier categorical taxonomy verification.
    2. Citation grounding against retrieved evidence.
    3. Deterministic calculations (chemical dilution, N-P-K balances, thermal conduciveness).
    4. Diagnostic boundary enforcement (no absolute unconfirmed assertions).
    5. Calibrated multidimensional confidence calculation.
    """
    logger.info("Executing Verification and Critic Node")

    synthesis_data = state.intermediate_results.get("synthesis", {})
    if not synthesis_data:
        state.verification_result = VerificationResult(
            overall_status=VerificationStatus.FAILED,
            missing_information=["Synthesis intermediate output is missing."],
        )
        return state

    # Extract multimodal metadata if available
    multimodal_meta = []
    for inp in state.request.inputs:
        multimodal_meta.append({
            "modality": inp.modality.value,
            "filename": inp.filename,
            "is_blurry": getattr(inp, "is_blurry", False),
        })

    # Run independent verification critic
    verification_res = VerificationCritic.evaluate_synthesis(
        candidate_response=synthesis_data,
        retrieved_evidence=state.retrieved_evidence,
        tool_results=state.tool_results,
        multimodal_metadata=multimodal_meta,
        missing_information=state.request_understanding.get("missing_information", []),
    )

    state.verification_result = verification_res

    logger.info(
        f"Verification completed: Status='{verification_res.overall_status.value}', "
        f"Passed={verification_res.passed_count}/{len(verification_res.checks)}, "
        f"HeuristicScore={verification_res.confidence.heuristic_score}"
    )
    return state
