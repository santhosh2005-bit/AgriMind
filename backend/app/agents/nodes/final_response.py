"""Node 9: Final Response Generation Node."""

import logging
from datetime import datetime, timezone
from backend.app.schemas.enums import VerificationStatus
from backend.app.schemas.response import FinalResponse
from backend.app.schemas.verification import ConfidenceBreakdown
from backend.app.agents.state import AgriMindState

logger = logging.getLogger("agrimind.node.final_response")


def final_response_node(state: AgriMindState) -> AgriMindState:
    """
    Assembles the final validated FinalResponse schema conforming to Section 9:
    - Request summary
    - Main answer
    - Observed facts
    - Retrieved evidence
    - Possible explanations (non-definitive)
    - Recommendations / next steps
    - Uncertainties and limitations
    - Source references
    - Verification status
    - Confidence indicators
    - Trace reference
    """
    logger.info("Executing Final Response Generation Node")

    synthesis = state.intermediate_results.get("synthesis", {})
    verif = state.verification_result

    domain_str = state.request_understanding.get("domain_category", "agriculture")
    if domain_str == "agriculture":
        crop = state.request_understanding.get("primary_crop", "crop")
        summary = f"Inquiry regarding {crop} with {len(state.detected_modalities)} input modalities."
    else:
        domain_label = domain_str.replace("_", " ").title()
        q_preview = state.request.text_query[:50] + ("..." if len(state.request.text_query) > 50 else "")
        summary = f"{domain_label} inquiry: \"{q_preview}\" with {len(state.detected_modalities)} input modalities."

    main_answer = synthesis.get(
        "main_answer",
        "Analysis could not be fully synthesized due to processing constraints."
    )
    observed_facts = synthesis.get("observed_facts", [])
    possible_causes = synthesis.get("possible_causes", [])
    recommendations = synthesis.get("recommendations", [])
    follow_up_questions = synthesis.get("follow_up_questions", [])
    visualizations = synthesis.get("visualizations", [])
    uncertainties = synthesis.get("uncertainties_and_limitations", [])
    sources = synthesis.get("source_references", [])

    verification_status = verif.overall_status if verif else VerificationStatus.NEEDS_REVIEW
    confidence_indicators = verif.confidence if verif else ConfidenceBreakdown()

    from backend.app.schemas.enums import SupportedLanguage
    target_lang_str = state.request_understanding.get("target_language", "en")
    try:
        resp_lang = SupportedLanguage(target_lang_str)
    except ValueError:
        resp_lang = SupportedLanguage.ENGLISH

    # Complete trace
    state.trace.completed_at = datetime.now(timezone.utc)
    state.trace.plan_id = state.execution_plan.plan_id if state.execution_plan else None

    state.final_response = FinalResponse(
        request_id=state.request.request_id,
        request_summary=summary,
        main_answer=main_answer,
        observed_facts=observed_facts,
        retrieved_evidence=state.retrieved_evidence,
        possible_causes=possible_causes,
        recommendations=recommendations,
        follow_up_questions=follow_up_questions,
        visualizations=visualizations,
        uncertainties_and_limitations=uncertainties,
        source_references=sources,
        verification_status=verification_status,
        confidence_indicators=confidence_indicators,
        language=resp_lang,
        trace_id=state.trace.trace_id,
    )

    state.is_completed = True
    logger.info(f"Final response produced successfully for request '{state.request.request_id}'")
    return state
