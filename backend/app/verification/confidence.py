"""Calibrated multidimensional confidence scoring engine.

Avoids relying on raw, uncalibrated LLM self-confidence or arbitrary percentages.
Instead, calculates confidence using a transparent weighted composite of four
empirically verifiable dimensions:
1. Grounding Score (35%): Evidence-to-claim alignment and citation validity.
2. Evidence Density Score (25%): Quality and relevance of retrieved ICAR/Open-Meteo data.
3. Calculation Validity Score (20%): Proportion of deterministic Python math checks passed.
4. Input Completeness Score (20%): Clarity of images, presence of weather, and absence of input gaps.
"""

from typing import List, Dict, Any, Optional
from backend.app.schemas.enums import ConfidenceLevel, VerificationStatus
from backend.app.schemas.verification import ConfidenceBreakdown, VerificationCheck


class ConfidenceCalculator:
    """Evaluates and produces transparent, auditable confidence breakdowns."""

    WEIGHT_GROUNDING = 0.35
    WEIGHT_EVIDENCE_DENSITY = 0.25
    WEIGHT_CALCULATION_VALIDITY = 0.20
    WEIGHT_INPUT_COMPLETENESS = 0.20

    @classmethod
    def calculate_confidence(
        cls,
        checks: List[VerificationCheck],
        evidence_count: int,
        missing_information_count: int,
        has_blurry_image: bool = False,
        has_unsupported_claims: bool = False,
    ) -> ConfidenceBreakdown:
        """
        Calculates multidimensional confidence breakdown conforming to competition specs.
        """
        # 1. Calculation Validity Score
        calc_checks = [c for c in checks if c.check_type == "deterministic_calculation"]
        if calc_checks:
            calc_passed = sum(1 for c in calc_checks if c.status == VerificationStatus.PASSED)
            calc_score = calc_passed / len(calc_checks)
        else:
            calc_score = 0.9  # No calculations flagged to fail

        # 2. Evidence Density Score
        if evidence_count >= 3:
            density_score = 1.0
        elif evidence_count == 2:
            density_score = 0.85
        elif evidence_count == 1:
            density_score = 0.70
        else:
            density_score = 0.35  # Unsupported by external knowledge base

        # 3. Grounding Score
        grounding_checks = [c for c in checks if c.check_type == "evidence_grounding"]
        if grounding_checks:
            grounding_passed = sum(1 for c in grounding_checks if c.status == VerificationStatus.PASSED)
            grounding_score = grounding_passed / len(grounding_checks)
        else:
            grounding_score = 0.8 if evidence_count > 0 else 0.4

        if has_unsupported_claims:
            grounding_score = max(0.0, grounding_score - 0.3)

        # 4. Input Completeness Score
        completeness_score = 1.0
        if missing_information_count > 0:
            completeness_score -= min(0.5, missing_information_count * 0.2)
        if has_blurry_image:
            completeness_score -= 0.25

        completeness_score = max(0.1, round(completeness_score, 3))

        # Composite Weighted Calculation
        composite = round(
            cls.WEIGHT_GROUNDING * grounding_score
            + cls.WEIGHT_EVIDENCE_DENSITY * density_score
            + cls.WEIGHT_CALCULATION_VALIDITY * calc_score
            + cls.WEIGHT_INPUT_COMPLETENESS * completeness_score,
            3,
        )

        # Determine qualitative confidence category
        if composite >= 0.82 and not has_unsupported_claims:
            level = ConfidenceLevel.HIGH
        elif composite >= 0.60:
            level = ConfidenceLevel.MEDIUM
        elif composite >= 0.40:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.UNCERTAIN

        formula_text = (
            f"Composite = 0.35*Grounding({grounding_score}) + "
            f"0.25*Density({density_score}) + "
            f"0.20*Calculations({calc_score}) + "
            f"0.20*Completeness({completeness_score}) = {composite:.3f}"
        )

        return ConfidenceBreakdown(
            evidence_coverage_score=round(grounding_score, 3),
            schema_validity_score=round(calc_score, 3),
            data_completeness_score=round(completeness_score, 3),
            overall_confidence=level,
            heuristic_score=composite,
            formula_explanation=formula_text,
        )
