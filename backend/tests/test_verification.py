"""Unit tests for Phase 7: Verification, Critic, Confidence & Recovery Engine.

Tests:
1. AgronomicCalculators: Chemical dilution, urea fertilizer math, split schedules, microclimates, soil sanity.
2. ConfidenceCalculator: Transparent multidimensional weighting and tier calibration.
3. VerificationCritic: Category partitioning, citation grounding, calculation audit, boundary audit.
4. Recovery Node: Autonomous self-correction, hazard neutralization, and RecoveryEvent telemetry.
"""

import unittest
from backend.app.schemas.enums import VerificationStatus, ConfidenceLevel, RecoveryAction, TaskType, ToolStatus
from backend.app.schemas.tools import RetrievedEvidence, ToolResult
from backend.app.schemas.request import UserRequest
from backend.app.agents.state import AgriMindState
from backend.app.verification.calculators import AgronomicCalculators
from backend.app.verification.confidence import ConfidenceCalculator
from backend.app.verification.critic import VerificationCritic
from backend.app.agents.nodes.recovery import recovery_node


class TestVerificationAndCritic(unittest.TestCase):
    """Test suite for independent verification, calculations, and recovery."""

    # -------------------------------------------------------------
    # 1. Deterministic Calculation Tests
    # -------------------------------------------------------------
    def test_chemical_dilution_correct(self):
        """1.0 ml/L in 500 L water = 500 ml."""
        res = AgronomicCalculators.verify_chemical_dilution(
            concentration_per_litre=1.0,
            spray_volume_litres=500.0,
            claimed_total_chemical=500.0,
            unit="ml"
        )
        self.assertTrue(res.is_valid)
        self.assertEqual(res.expected_value, 500.0)
        self.assertEqual(len(res.warnings), 0)

    def test_chemical_dilution_mismatch(self):
        """Mismatch: Claimed 250 ml when 1 ml/L in 500 L equals 500 ml."""
        res = AgronomicCalculators.verify_chemical_dilution(
            concentration_per_litre=1.0,
            spray_volume_litres=500.0,
            claimed_total_chemical=250.0,
            unit="ml"
        )
        self.assertFalse(res.is_valid)
        self.assertGreater(len(res.warnings), 0)
        self.assertIn("mismatch", res.warnings[0].lower())

    def test_urea_from_nitrogen_balance(self):
        """120 kg N / 0.46 = 260.87 kg Urea."""
        res = AgronomicCalculators.verify_urea_from_nitrogen(
            target_n_kg_ha=120.0,
            claimed_urea_kg_ha=260.87
        )
        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(res.expected_value, 260.87, places=1)

    def test_urea_calculation_error(self):
        """Advisory claims 120 kg Urea for 120 kg N (forgetting 46% concentration)."""
        res = AgronomicCalculators.verify_urea_from_nitrogen(
            target_n_kg_ha=120.0,
            claimed_urea_kg_ha=120.0
        )
        self.assertFalse(res.is_valid)
        self.assertIn("calculation error", res.warnings[0].lower())

    def test_split_application_schedule_valid(self):
        """Basal 50% + CRI 25% + Jointing 25% = 100%."""
        res = AgronomicCalculators.verify_split_application_schedule([0.5, 0.25, 0.25])
        self.assertTrue(res.is_valid)

    def test_split_application_schedule_invalid(self):
        """Splits summing to 80% should fail validation."""
        res = AgronomicCalculators.verify_split_application_schedule([0.5, 0.3])
        self.assertFalse(res.is_valid)
        self.assertIn("Split schedule arithmetic invalid", res.warnings[0])

    def test_disease_microclimate_yellow_rust_arrested(self):
        """Yellow rust development is arrested above 25°C."""
        res = AgronomicCalculators.verify_disease_weather_conduciveness(
            pathogen_or_disease="Yellow Rust",
            temperature_c=29.5,
            relative_humidity_pct=60.0
        )
        self.assertFalse(res.is_valid)
        self.assertIn("arrested", res.warnings[0].lower())

    def test_soil_amendment_sanity_lime_on_alkaline_soil(self):
        """Applying lime to alkaline soil (pH >= 7.5) is a hazardous contradiction."""
        res = AgronomicCalculators.verify_soil_amendment_sanity(
            soil_ph=7.8,
            proposed_amendment="Agricultural lime application at 2 tons/ha"
        )
        self.assertFalse(res.is_valid)
        self.assertIn("CRITICAL AGRONOMIC HAZARD", res.warnings[0])

    def test_soil_amendment_sanity_gypsum_on_alkaline_soil(self):
        """Gypsum on alkaline soil is safe and agronomically recommended."""
        res = AgronomicCalculators.verify_soil_amendment_sanity(
            soil_ph=7.8,
            proposed_amendment="Gypsum application at 1.5 tons/ha"
        )
        self.assertTrue(res.is_valid)

    # -------------------------------------------------------------
    # 2. Confidence Calibration Tests
    # -------------------------------------------------------------
    def test_confidence_calibration_high(self):
        """High evidence density + 0 ungrounded claims + 0 gaps -> HIGH confidence."""
        breakdown = ConfidenceCalculator.calculate_confidence(
            checks=[],
            evidence_count=3,
            missing_information_count=0,
            has_blurry_image=False,
            has_unsupported_claims=False
        )
        self.assertEqual(breakdown.overall_confidence, ConfidenceLevel.HIGH)
        self.assertGreaterEqual(breakdown.heuristic_score, 0.82)
        self.assertIn("0.35*Grounding", breakdown.formula_explanation)

    def test_confidence_calibration_low_when_ungrounded(self):
        """Unsupported claims throttle confidence level."""
        breakdown = ConfidenceCalculator.calculate_confidence(
            checks=[],
            evidence_count=0,
            missing_information_count=2,
            has_blurry_image=True,
            has_unsupported_claims=True
        )
        self.assertIn(breakdown.overall_confidence, [ConfidenceLevel.LOW, ConfidenceLevel.UNCERTAIN])
        self.assertLess(breakdown.heuristic_score, 0.60)

    # -------------------------------------------------------------
    # 3. VerificationCritic Tests
    # -------------------------------------------------------------
    def test_critic_flags_ungrounded_chemical(self):
        """Critic must detect when recommended chemical does not exist in retrieved evidence."""
        evidence = [
            RetrievedEvidence(
                source_type="advisory_document",
                source_name="ICAR_Tomato_Advisory.pdf",
                location_reference="Section 2",
                content_snippet="Recommend spraying Mancozeb @ 2.5 g/litre for early blight management.",
                relevance_score=0.95
            )
        ]
        # Candidate recommends Carbendazim which is NOT in retrieved evidence
        candidate = {
            "main_answer": "Treat the foliar symptoms using chemical control.",
            "observed_facts": ["Yellowing and brown spots on tomato foliage."],
            "possible_causes": ["Early blight fungal infection."],
            "recommendations": ["Apply Carbendazim 50% WP spray immediately."],
            "uncertainties_and_limitations": ["Visual diagnosis requires laboratory confirmation."]
        }
        verif = VerificationCritic.evaluate_synthesis(candidate, evidence)
        self.assertEqual(verif.overall_status, VerificationStatus.FAILED)
        self.assertTrue(any("lacks grounding" in c for c in verif.conflicts_detected))

    def test_critic_boundary_enforcement(self):
        """Critic rejects absolute claims like '100% confirmed' without lab tests."""
        evidence = [
            RetrievedEvidence(
                source_type="advisory_document",
                source_name="ICAR_Tomato_Advisory.pdf",
                content_snippet="Mancozeb 2.5 g/L",
                relevance_score=0.9
            )
        ]
        candidate = {
            "main_answer": "The crop is 100% confirmed to have late blight.",
            "observed_facts": ["Leaf spots."],
            "possible_causes": ["Late blight."],
            "recommendations": ["Apply Mancozeb."],
            "uncertainties_and_limitations": []  # Missing lab assay disclaimer
        }
        verif = VerificationCritic.evaluate_synthesis(candidate, evidence)
        self.assertEqual(verif.overall_status, VerificationStatus.FAILED)
        boundary_checks = [c for c in verif.checks if c.check_type == "boundary_enforcement"]
        self.assertEqual(boundary_checks[0].status, VerificationStatus.FAILED)

    # -------------------------------------------------------------
    # 4. Recovery Node Self-Correction Tests
    # -------------------------------------------------------------
    def test_recovery_node_corrects_alkaline_soil_lime_hazard(self):
        """Recovery node must substitute lime with gypsum on alkaline soil and log a RecoveryEvent."""
        state = AgriMindState(
            request=UserRequest(
                text_query="Provide soil management advice for parcel P-101. Soil pH is 7.8 alkaline."
            )
        )
        state.intermediate_results["synthesis"] = {
            "main_answer": "Adjust soil chemistry to improve crop yield.",
            "observed_facts": ["Soil pH tested at 7.8."],
            "possible_causes": ["Alkalinity stress."],
            "recommendations": ["Apply agricultural lime at 2 tons/ha to treat soil."],
            "uncertainties_and_limitations": []
        }
        # Simulate critic failing due to lime on alkaline soil
        evidence = [RetrievedEvidence(source_type="general", source_name="KB", content_snippet="Gypsum application", relevance_score=0.9)]
        tool_results = {
            "soil": ToolResult(
                invocation_id="test-soil-inv",
                tool_name="structured_data_query",
                status=ToolStatus.SUCCESS,
                structured_data={"records": [{"parcel_id": "P-101", "soil_ph": 7.8}]}
            )
        }
        verif = VerificationCritic.evaluate_synthesis(
            candidate_response=state.intermediate_results["synthesis"],
            retrieved_evidence=evidence,
            tool_results=tool_results
        )
        state.verification_result = verif
        self.assertEqual(verif.overall_status, VerificationStatus.FAILED)

        # Run recovery node
        recovered_state = recovery_node(state)

        # Check self-correction
        recs = recovered_state.intermediate_results["synthesis"]["recommendations"]
        recs_str = " ".join(recs)
        self.assertNotIn("lime at", recs_str.lower())
        self.assertIn("gypsum", recs_str.lower())
        self.assertGreater(len(recovered_state.recovery_events), 0)
        self.assertEqual(recovered_state.recovery_events[0].action_taken, RecoveryAction.RETRY_WITH_CONSTRAINTS)
        self.assertEqual(recovered_state.verification_result.overall_status, VerificationStatus.PASSED_WITH_LIMITATIONS)


if __name__ == "__main__":
    unittest.main()
