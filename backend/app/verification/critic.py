"""Independent Verification and Critic Evaluator.

Evaluates synthesized candidate responses prior to final delivery to the user:
1. Distinct factual category taxonomy (observed vs retrieved vs hypothesis vs uncertainty).
2. Citation grounding against retrieved evidence passages.
3. Deterministic agronomic and biochemical calculation audits.
4. Contradiction and hazard detection (e.g. lime on alkaline soil, out-of-bounds microclimates).
5. Diagnostic boundary enforcement (no unverified absolute pathogen claims).
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from backend.app.schemas.enums import VerificationStatus, ConfidenceLevel
from backend.app.schemas.tools import RetrievedEvidence
from backend.app.schemas.verification import (
    VerificationResult,
    VerificationCheck,
    ConfidenceBreakdown,
)
from backend.app.verification.calculators import AgronomicCalculators, CalculationResult
from backend.app.verification.confidence import ConfidenceCalculator

logger = logging.getLogger("agrimind.verification.critic")


class VerificationCritic:
    """Rigorous independent critic validating agronomic correctness, citations, and calculations."""

    @classmethod
    def evaluate_synthesis(
        cls,
        candidate_response: Dict[str, Any],
        retrieved_evidence: List[RetrievedEvidence],
        tool_results: Optional[Dict[str, Any]] = None,
        multimodal_metadata: Optional[List[Dict[str, Any]]] = None,
        missing_information: Optional[List[str]] = None,
    ) -> VerificationResult:
        """
        Runs comprehensive suite of deterministic checks on the candidate synthesis.
        """
        checks: List[VerificationCheck] = []
        conflicts_detected: List[str] = []
        tool_results = tool_results or {}
        missing_information = missing_information or []

        main_answer = candidate_response.get("main_answer", "")
        observed_facts = candidate_response.get("observed_facts", [])
        possible_causes = candidate_response.get("possible_causes", [])
        recommendations = candidate_response.get("recommendations", [])
        uncertainties = candidate_response.get("uncertainties_and_limitations", [])

        # ---------------------------------------------------------
        # Check 1: Categorical Partitioning & Structural Integrity
        # ---------------------------------------------------------
        required_fields = {
            "main_answer": bool(main_answer and len(main_answer) >= 15),
            "observed_facts": bool(observed_facts),
            "possible_causes": bool(possible_causes),
            "recommendations": bool(recommendations),
            "uncertainties_and_limitations": bool(uncertainties),
        }
        all_categories_valid = all(required_fields.values())
        checks.append(
            VerificationCheck(
                check_type="categorical_taxonomy",
                status=VerificationStatus.PASSED if all_categories_valid else VerificationStatus.FAILED,
                details=(
                    f"Verified 5-tier classification (observed symptoms, evidence, causes, recommendations, uncertainties). "
                    f"Present: {[k for k, v in required_fields.items() if v]}"
                ),
                deterministic_passed=all_categories_valid,
            )
        )

        # ---------------------------------------------------------
        # Check 2: Citation Grounding of Interventions
        # ---------------------------------------------------------
        evidence_corpus_text = " ".join([e.content_snippet.lower() for e in retrieved_evidence])
        recs_text = " ".join(recommendations).lower()
        full_text = f"{main_answer} {recs_text}".lower()

        # Extract common active chemical ingredients to verify grounding
        known_agrochemicals = [
            "propiconazole", "tebuconazole", "mancozeb", "imidacloprid",
            "chlorpyrifos", "copper oxychloride", "carbendazim", "azoxystrobin",
            "thiamethoxam", "urea", "dap", "gypsum", "lime"
        ]
        recommended_chemicals = [chem for chem in known_agrochemicals if chem in recs_text]

        unsupported_chemicals = []
        for chem in recommended_chemicals:
            if chem not in evidence_corpus_text:
                unsupported_chemicals.append(chem)

        if unsupported_chemicals:
            has_unsupported = True
            checks.append(
                VerificationCheck(
                    check_type="evidence_grounding",
                    status=VerificationStatus.FAILED,
                    target_claim=f"Chemical recommendation: {', '.join(unsupported_chemicals)}",
                    details=(
                        f"UNGROUNDED INTERVENTION: Recommended chemical(s) '{', '.join(unsupported_chemicals)}' "
                        f"do not appear in any retrieved ICAR advisory documents or evidence passages."
                    ),
                    deterministic_passed=False,
                )
            )
            conflicts_detected.append(
                f"Chemical recommendation '{', '.join(unsupported_chemicals)}' lacks grounding in retrieved evidence."
            )
        else:
            has_unsupported = False
            checks.append(
                VerificationCheck(
                    check_type="evidence_grounding",
                    status=VerificationStatus.PASSED if retrieved_evidence else VerificationStatus.PASSED_WITH_LIMITATIONS,
                    details=(
                        f"All {len(recommended_chemicals)} recommended chemical active ingredients are substantiated "
                        f"by {len(retrieved_evidence)} retrieved evidence citations."
                    ),
                    supporting_evidence_ids=[e.evidence_id for e in retrieved_evidence],
                    deterministic_passed=True,
                )
            )

        # ---------------------------------------------------------
        # Check 3: Deterministic Calculation Validation
        # ---------------------------------------------------------
        # 3A. Chemical Dilution Check
        dilution_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:ml|g)\s*(?:per|\/)\s*(?:litre|l)", full_text)
        volume_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:litres?|l)\s*(?:of\s+water|total)", full_text)
        claimed_total_match = re.search(r"total\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*(?:ml|g|litres?)", full_text)

        if dilution_match and volume_match and claimed_total_match:
            conc = float(dilution_match.group(1))
            vol = float(volume_match.group(1))
            claimed_tot = float(claimed_total_match.group(1))
            calc_res = AgronomicCalculators.verify_chemical_dilution(conc, vol, claimed_tot)
            checks.append(
                VerificationCheck(
                    check_type="deterministic_calculation",
                    status=VerificationStatus.PASSED if calc_res.is_valid else VerificationStatus.FAILED,
                    target_claim=f"Dilution math: {conc} unit/L in {vol} L",
                    details=calc_res.explanation,
                    deterministic_passed=calc_res.is_valid,
                )
            )
            if not calc_res.is_valid:
                conflicts_detected.extend(calc_res.warnings)

        # 3B. Nitrogen to Urea Conversion Check
        nitrogen_match = re.search(r"(\d+(?:\.\d+)?)\s*kg\s*n\s*(?:\/|\s*per\s*)ha", full_text)
        urea_match = re.search(r"(\d+(?:\.\d+)?)\s*kg\s*urea", full_text)
        if nitrogen_match and urea_match:
            target_n = float(nitrogen_match.group(1))
            claimed_urea = float(urea_match.group(1))
            urea_res = AgronomicCalculators.verify_urea_from_nitrogen(target_n, claimed_urea)
            checks.append(
                VerificationCheck(
                    check_type="deterministic_calculation",
                    status=VerificationStatus.PASSED if urea_res.is_valid else VerificationStatus.FAILED,
                    target_claim=f"Fertilizer balance: {target_n} kg N -> {claimed_urea} kg Urea",
                    details=urea_res.explanation,
                    deterministic_passed=urea_res.is_valid,
                )
            )
            if not urea_res.is_valid:
                conflicts_detected.extend(urea_res.warnings)

        # 3C. Weather & Disease Microclimate Feasibility
        weather_res = next((res for res in tool_results.values() if getattr(res, "tool_name", "") == "weather_connector"), None)
        if weather_res and getattr(weather_res, "structured_data", None):
            temp_max = weather_res.structured_data.get("temp_max_c", 25.0)
            humidity = weather_res.structured_data.get("relative_humidity_pct", 65.0)

            for disease_candidate in ["yellow rust", "whitefly", "late blight"]:
                if disease_candidate in full_text:
                    weath_check = AgronomicCalculators.verify_disease_weather_conduciveness(
                        disease_candidate, temp_max, humidity
                    )
                    checks.append(
                        VerificationCheck(
                            check_type="deterministic_calculation",
                            status=VerificationStatus.PASSED if weath_check.is_valid else VerificationStatus.FAILED,
                            target_claim=f"Microclimate validation for {disease_candidate}",
                            details=weath_check.explanation,
                            deterministic_passed=weath_check.is_valid,
                        )
                    )
                    if not weath_check.is_valid:
                        conflicts_detected.extend(weath_check.warnings)

        # 3D. Soil pH Amendment Sanity Check
        soil_res = next((res for res in tool_results.values() if getattr(res, "tool_name", "") == "structured_data_query"), None)
        soil_ph = None
        if soil_res and getattr(soil_res, "structured_data", None):
            records = soil_res.structured_data.get("records", [])
            if records and "soil_ph" in records[0]:
                soil_ph = float(records[0]["soil_ph"])

        if soil_ph is not None:
            for amendment in ["lime", "calcium carbonate", "gypsum", "sulfur"]:
                if amendment in recs_text:
                    amend_check = AgronomicCalculators.verify_soil_amendment_sanity(soil_ph, amendment)
                    checks.append(
                        VerificationCheck(
                            check_type="deterministic_calculation",
                            status=VerificationStatus.PASSED if amend_check.is_valid else VerificationStatus.FAILED,
                            target_claim=f"Soil amendment {amendment} for soil pH {soil_ph}",
                            details=amend_check.explanation,
                            deterministic_passed=amend_check.is_valid,
                        )
                    )
                    if not amend_check.is_valid:
                        conflicts_detected.extend(amend_check.warnings)

        # ---------------------------------------------------------
        # Check 4: Diagnostic Boundary & Honest Uncertainty Enforcement
        # ---------------------------------------------------------
        absolute_assertions = [
            "100% confirmed", "definitely caused by", "unquestionably infected",
            "proven diagnosis", "guaranteed eradication", "definitive proof"
        ]
        has_absolute_claim = any(assertion in full_text for assertion in absolute_assertions)
        valid_caveats = [
            "laboratory", "assay", "pcr", "soil test", "sample", "cannot definitively confirm",
            "limit", "assumes", "precision", "rounding", "version", "scope", "omitted",
            "publicly indexed", "boundary", "dependency", "nuance", "uncertain"
        ]
        has_uncertainty_disclaimer = any(
            any(caveat in u.lower() for caveat in valid_caveats)
            for u in uncertainties
        )

        boundary_passed = (not has_absolute_claim) and has_uncertainty_disclaimer
        checks.append(
            VerificationCheck(
                check_type="boundary_enforcement",
                status=VerificationStatus.PASSED if boundary_passed else VerificationStatus.FAILED,
                details=(
                    f"Boundary audit: Absolute claims avoided: {not has_absolute_claim}. "
                    f"Honest domain uncertainty caveats present: {has_uncertainty_disclaimer}."
                ),
                deterministic_passed=boundary_passed,
            )
        )
        if has_absolute_claim:
            conflicts_detected.append("Advisory contains uncalibrated absolute claims without required confirmation.")
        if not has_uncertainty_disclaimer:
            conflicts_detected.append("Advisory lacks mandatory uncertainty caveats.")

        # ---------------------------------------------------------
        # Check 5: Multimodal Quality Consideration
        # ---------------------------------------------------------
        is_blurry = False
        if multimodal_metadata:
            for meta in multimodal_metadata:
                if isinstance(meta, dict) and meta.get("is_blurry", False):
                    is_blurry = True
                    checks.append(
                        VerificationCheck(
                            check_type="input_quality",
                            status=VerificationStatus.PASSED_WITH_LIMITATIONS,
                            details="Photographic input exhibits low Laplacian clarity score; visual confidence throttled.",
                            deterministic_passed=True,
                        )
                    )

        # ---------------------------------------------------------
        # Calibrated Multidimensional Confidence Score
        # ---------------------------------------------------------
        confidence = ConfidenceCalculator.calculate_confidence(
            checks=checks,
            evidence_count=len(retrieved_evidence),
            missing_information_count=len(missing_information),
            has_blurry_image=is_blurry,
            has_unsupported_claims=has_unsupported,
        )

        # Overall Status Determination
        failed_count = sum(1 for c in checks if c.status == VerificationStatus.FAILED)
        if failed_count > 0:
            overall_status = VerificationStatus.FAILED
        elif conflicts_detected:
            overall_status = VerificationStatus.NEEDS_REVIEW
        elif confidence.overall_confidence == ConfidenceLevel.HIGH:
            overall_status = VerificationStatus.PASSED
        else:
            overall_status = VerificationStatus.PASSED_WITH_LIMITATIONS

        return VerificationResult(
            overall_status=overall_status,
            checks=checks,
            confidence=confidence,
            missing_information=missing_information,
            conflicts_detected=conflicts_detected,
        )
