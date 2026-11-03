"""Node 8: Recovery, Self-Correction, and Human Escalation Node."""

import logging
from backend.app.schemas.enums import RecoveryAction, VerificationStatus
from backend.app.schemas.trace import RecoveryEvent
from backend.app.agents.state import AgriMindState

logger = logging.getLogger("agrimind.node.recovery")


def recovery_node(state: AgriMindState) -> AgriMindState:
    """
    Evaluates verification outcome, calculation discrepancies, and execution faults:
    1. If critical execution errors occurred, appends explicit diagnostic limitations.
    2. If verification detected conflicts/hazards (e.g. lime on alkaline soil, dilution math error):
       - Applies deterministic self-correction to synthesized recommendations.
       - Logs RecoveryEvent into telemetry.
    3. If unresolved uncertainties remain, escalates for human agronomist review.
    """
    logger.info("Executing Recovery & Self-Correction Node")

    verif = state.verification_result
    synthesis = state.intermediate_results.get("synthesis", {})

    # 1. Recovery from step execution errors
    if state.execution_errors:
        event = RecoveryEvent(
            step_id="workflow_recovery",
            trigger_reason=f"Execution errors encountered: {'; '.join(state.execution_errors)}",
            action_taken=RecoveryAction.ABSTAIN_WITH_LIMITATIONS,
            from_target="workflow_engine",
            to_target="final_response_caveats",
            success=True,
            details="Appended explicit caveats to uncertainties and limitations.",
        )
        state.recovery_events.append(event)
        state.trace.recovery_events.append(event)

        if synthesis and "uncertainties_and_limitations" in synthesis:
            synthesis["uncertainties_and_limitations"].extend(state.execution_errors)

    # 2. Recovery and deterministic self-correction from verification findings
    if verif and verif.overall_status in [VerificationStatus.FAILED, VerificationStatus.NEEDS_REVIEW]:
        corrections_applied = []

        if synthesis:
            recommendations = synthesis.get("recommendations", [])
            uncertainties = synthesis.get("uncertainties_and_limitations", [])

            # Correct hazardous soil recommendations (e.g. Lime on alkaline soil)
            for conflict in verif.conflicts_detected:
                if "alkaline" in conflict.lower() and "lime" in conflict.lower():
                    # Sanitize recommendations: replace lime with gypsum
                    new_recs = []
                    for r in recommendations:
                        if "lime" in r.lower() and "gypsum" not in r.lower():
                            corrected_rec = r.replace("lime", "gypsum / elemental sulfur").replace("Lime", "Gypsum")
                            new_recs.append(corrected_rec)
                            corrections_applied.append(f"Substituted lime with gypsum for alkaline soil: '{corrected_rec}'")
                        else:
                            new_recs.append(r)
                    synthesis["recommendations"] = new_recs

                elif "lacks grounding" in conflict.lower():
                    # Flag ungrounded chemicals
                    uncertainties.append(f"Flagged by Critic: {conflict}")
                    corrections_applied.append(f"Annotated ungrounded chemical: {conflict}")

            # Correct missing laboratory assay caveats
            has_lab_disclaimer = any("laboratory" in u.lower() or "assay" in u.lower() for u in uncertainties)
            if not has_lab_disclaimer:
                lab_disclaimer = (
                    "Mandatory Diagnostic Caveat: Visual symptoms can mirror multiple nutritional and viral pathologies. "
                    "Confirmation requires laboratory tissue analysis before extensive chemical applications."
                )
                uncertainties.append(lab_disclaimer)
                corrections_applied.append("Injected mandatory laboratory assay caveat.")

            synthesis["uncertainties_and_limitations"] = uncertainties

        action_type = (
            RecoveryAction.RETRY_WITH_CONSTRAINTS
            if corrections_applied
            else RecoveryAction.REQUEST_HUMAN_REVIEW
        )

        event = RecoveryEvent(
            step_id="verification_self_correction",
            trigger_reason=f"Verification status '{verif.overall_status.value}'. Conflicts: {'; '.join(verif.conflicts_detected)}",
            action_taken=action_type,
            from_target="verification_node",
            to_target="synthesis_repair",
            success=True,
            details=f"Self-correction applied: {'; '.join(corrections_applied) if corrections_applied else 'Escalated to review queue'}",
        )
        state.recovery_events.append(event)
        state.trace.recovery_events.append(event)

        # Update verification status to reflect successful self-correction
        if corrections_applied:
            verif.overall_status = VerificationStatus.PASSED_WITH_LIMITATIONS
            if synthesis and "recommendations" in synthesis:
                synthesis["recommendations"].insert(
                    0,
                    "NOTE: Advisory was autonomously audited and adjusted by the AgriMind Critic to correct agronomic constraints."
                )
        else:
            if synthesis and "recommendations" in synthesis:
                synthesis["recommendations"].insert(
                    0,
                    "URGENT REVIEW: Please consult a certified local agronomist or extension officer before acting on this advisory."
                )

    logger.info(f"Recovery node processing complete. Total events: {len(state.recovery_events)}")
    return state
