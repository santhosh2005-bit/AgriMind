"""Deterministic agronomic calculation engines and consistency validators.

These pure-Python calculators independently verify AI recommendations against
established biochemical, physical, and agronomic formulas:
1. Chemical dilution & total spray volume checks.
2. Nitrogen (N) to Urea (46% N) and split scheduling arithmetic.
3. Disease microclimate feasibility (temperature and humidity bounds).
4. Soil amendment sanity checks (e.g. lime vs gypsum based on pH).
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class CalculationResult(BaseModel):
    is_valid: bool
    calculator_name: str
    expected_value: Any
    actual_value: Any
    margin_error_pct: float = 0.0
    explanation: str
    warnings: List[str] = Field(default_factory=list)


class AgronomicCalculators:
    """Pure deterministic calculation engine for agricultural advisory verification."""

    @staticmethod
    def verify_chemical_dilution(
        concentration_per_litre: float,
        spray_volume_litres: float,
        claimed_total_chemical: float,
        tolerance_pct: float = 2.0,
        unit: str = "ml",
    ) -> CalculationResult:
        """
        Verifies total chemical formulation requirement:
        Expected Total = Concentration (per L) * Total Spray Volume (L).
        Example: 1.0 ml/L * 500 L = 500 ml.
        """
        expected_total = round(concentration_per_litre * spray_volume_litres, 3)
        margin_error = 0.0
        if expected_total > 0:
            margin_error = abs(claimed_total_chemical - expected_total) / expected_total * 100.0

        is_valid = margin_error <= tolerance_pct
        warnings = []
        if not is_valid:
            warnings.append(
                f"Chemical dosage mismatch: Claimed {claimed_total_chemical} {unit}, "
                f"but {concentration_per_litre} {unit}/L in {spray_volume_litres} L equals {expected_total} {unit}."
            )

        explanation = (
            f"Calculated: {concentration_per_litre} {unit}/L * {spray_volume_litres} L = {expected_total} {unit}. "
            f"Claimed: {claimed_total_chemical} {unit} (Deviation: {margin_error:.2f}%)."
        )

        return CalculationResult(
            is_valid=is_valid,
            calculator_name="chemical_dilution",
            expected_value=expected_total,
            actual_value=claimed_total_chemical,
            margin_error_pct=round(margin_error, 2),
            explanation=explanation,
            warnings=warnings,
        )

    @staticmethod
    def verify_urea_from_nitrogen(
        target_n_kg_ha: float,
        claimed_urea_kg_ha: float,
        tolerance_pct: float = 3.0,
    ) -> CalculationResult:
        """
        Verifies Urea requirement from target Nitrogen.
        Commercial Urea contains 46% Nitrogen (0.46 kg N per kg Urea).
        Expected Urea (kg/ha) = Target N (kg/ha) / 0.46.
        Example: 120 kg N/ha / 0.46 = 260.87 kg Urea/ha.
        """
        expected_urea = round(target_n_kg_ha / 0.46, 2)
        margin_error = abs(claimed_urea_kg_ha - expected_urea) / expected_urea * 100.0 if expected_urea > 0 else 0.0

        is_valid = margin_error <= tolerance_pct
        warnings = []
        if not is_valid:
            warnings.append(
                f"Fertilizer N-P-K calculation error: Target N of {target_n_kg_ha} kg/ha requires "
                f"{expected_urea} kg Urea/ha (46% N), but advisory proposed {claimed_urea_kg_ha} kg Urea/ha."
            )

        explanation = (
            f"Urea conversion: {target_n_kg_ha} kg N / 0.46 = {expected_urea} kg Urea/ha. "
            f"Advisory claimed: {claimed_urea_kg_ha} kg Urea/ha (Deviation: {margin_error:.2f}%)."
        )

        return CalculationResult(
            is_valid=is_valid,
            calculator_name="nitrogen_urea_balance",
            expected_value=expected_urea,
            actual_value=claimed_urea_kg_ha,
            margin_error_pct=round(margin_error, 2),
            explanation=explanation,
            warnings=warnings,
        )

    @staticmethod
    def verify_split_application_schedule(
        proportions: List[float],
        tolerance_pct: float = 1.0,
    ) -> CalculationResult:
        """
        Verifies that fertilizer split schedule fractions sum to exactly 1.0 (100%).
        Example: Basal 50% (0.50) + CRI 25% (0.25) + Tillering 25% (0.25) = 1.0 (100%).
        """
        total = round(sum(proportions), 4)
        margin_error = abs(total - 1.0) * 100.0
        is_valid = margin_error <= tolerance_pct

        warnings = []
        if not is_valid:
            warnings.append(
                f"Split schedule arithmetic invalid: Splits sum to {total * 100:.1f}%, not 100%."
            )

        explanation = f"Fertilizer splits: {proportions} -> Total: {total * 100:.1f}%."

        return CalculationResult(
            is_valid=is_valid,
            calculator_name="fertilizer_split_schedule",
            expected_value=1.0,
            actual_value=total,
            margin_error_pct=round(margin_error, 2),
            explanation=explanation,
            warnings=warnings,
        )

    @staticmethod
    def verify_disease_weather_conduciveness(
        pathogen_or_disease: str,
        temperature_c: float,
        relative_humidity_pct: float,
    ) -> CalculationResult:
        """
        Checks epidemiological thresholds for common agricultural pathogens.
        - Yellow Rust (Wheat): Favorable 10-15°C and RH > 80%. Arrested > 25°C.
        - Whitefly (Tomato vector): Proliferates at 28-38°C and RH < 65%.
        - Late Blight: Favorable 12-20°C and RH > 85%.
        """
        disease_lower = pathogen_or_disease.lower()
        warnings = []
        is_conducive = False
        rule_desc = ""

        if "yellow rust" in disease_lower or "stripe rust" in disease_lower or "puccinia" in disease_lower:
            rule_desc = "Yellow Rust favorable: 10-15°C and RH > 80%; arrested > 25°C."
            if temperature_c > 25.0:
                is_conducive = False
                warnings.append(
                    f"Epidemiological contradiction: Yellow rust pathogen development is arrested at temperatures > 25°C (Observed: {temperature_c}°C)."
                )
            elif 10.0 <= temperature_c <= 18.0 and relative_humidity_pct >= 75.0:
                is_conducive = True
            else:
                is_conducive = False

        elif "whitefly" in disease_lower or "bemisia" in disease_lower or "leaf curl" in disease_lower:
            rule_desc = "Whitefly proliferation favorable: 28-38°C and moderate-to-low RH."
            if 28.0 <= temperature_c <= 40.0:
                is_conducive = True
            else:
                is_conducive = False

        elif "late blight" in disease_lower or "phytophthora" in disease_lower:
            rule_desc = "Late Blight favorable: 12-22°C and RH > 80%."
            if 12.0 <= temperature_c <= 22.0 and relative_humidity_pct >= 80.0:
                is_conducive = True
            else:
                is_conducive = False
        else:
            # Generic fallback
            rule_desc = "General fungal risk threshold: RH > 75%."
            is_conducive = relative_humidity_pct >= 75.0

        explanation = (
            f"Weather check ({rule_desc}): Observed Temp={temperature_c}°C, "
            f"RH={relative_humidity_pct}%. Microclimate conducive={is_conducive}."
        )

        return CalculationResult(
            is_valid=len(warnings) == 0,
            calculator_name="disease_weather_conduciveness",
            expected_value=True,
            actual_value=is_conducive,
            margin_error_pct=0.0,
            explanation=explanation,
            warnings=warnings,
        )

    @staticmethod
    def verify_soil_amendment_sanity(
        soil_ph: float,
        proposed_amendment: str,
    ) -> CalculationResult:
        """
        Agronomic sanity rule:
        - Agricultural Lime (calcium carbonate) raises pH. Safe ONLY on acidic soils (pH < 6.5).
          Applying lime to alkaline soil (pH > 7.5) causes severe nutrient lockout!
        - Gypsum (calcium sulfate) or elemental sulfur remediates alkaline/sodic soils without raising pH.
        """
        amendment_lower = proposed_amendment.lower()
        warnings = []
        is_safe = True

        if ("lime" in amendment_lower or "calcium carbonate" in amendment_lower) and "gypsum" not in amendment_lower:
            if soil_ph >= 7.5:
                is_safe = False
                warnings.append(
                    f"CRITICAL AGRONOMIC HAZARD: Advisory recommended lime application on soil with alkaline pH {soil_ph}. "
                    "Lime raises pH and will induce severe iron, manganese, and zinc deficiency. Gypsum or sulfur should be used instead."
                )

        if ("sulfur" in amendment_lower or "gypsum" in amendment_lower) and soil_ph < 5.5:
            warnings.append(
                f"Caution: Soil is strongly acidic (pH {soil_ph}). Acidifying amendments may aggravate aluminum toxicity."
            )

        explanation = f"Soil pH={soil_ph}, Proposed amendment='{proposed_amendment}'. Agronomic safety verified: {is_safe}."

        return CalculationResult(
            is_valid=is_safe,
            calculator_name="soil_amendment_sanity",
            expected_value="safe_amendment",
            actual_value="safe" if is_safe else "hazardous_recommendation",
            margin_error_pct=0.0,
            explanation=explanation,
            warnings=warnings,
        )

    @staticmethod
    def evaluate_safe_math(
        expression: str,
        claimed_result: Optional[float] = None,
        tolerance_pct: float = 1.0,
    ) -> CalculationResult:
        """
        Safely evaluates general mathematical expressions (arithmetic, percentages, powers, ratios)
        using deterministic AST evaluation without unsafe exec/eval.
        """
        import ast
        import operator

        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        def _eval_node(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return float(node.value)
            elif isinstance(node, ast.BinOp):
                left = _eval_node(node.left)
                right = _eval_node(node.right)
                op_type = type(node.op)
                if op_type in ops:
                    return ops[op_type](left, right)
                raise ValueError(f"Unsupported operator: {op_type}")
            elif isinstance(node, ast.UnaryOp):
                operand = _eval_node(node.operand)
                op_type = type(node.op)
                if op_type in ops:
                    return ops[op_type](operand)
                raise ValueError(f"Unsupported unary operator: {op_type}")
            raise ValueError(f"Unsupported syntax in math expression: {type(node)}")

        clean_expr = expression.replace(",", "").replace("^", "**").replace("%", "/100.0").strip()
        try:
            tree = ast.parse(clean_expr, mode="eval")
            calc_val = round(_eval_node(tree.body), 4)

            margin_error = 0.0
            is_valid = True
            warnings = []
            if claimed_result is not None:
                if calc_val != 0.0:
                    margin_error = round(abs(claimed_result - calc_val) / abs(calc_val) * 100.0, 2)
                else:
                    margin_error = 0.0 if claimed_result == 0.0 else 100.0
                is_valid = margin_error <= tolerance_pct
                if not is_valid:
                    warnings.append(
                        f"Calculation discrepancy: evaluated {expression} = {calc_val}, but claimed {claimed_result} (error {margin_error}%)."
                    )

            return CalculationResult(
                is_valid=is_valid,
                calculator_name="safe_math_evaluator",
                expected_value=calc_val,
                actual_value=claimed_result if claimed_result is not None else calc_val,
                margin_error_pct=margin_error,
                explanation=f"Evaluated expression '{expression}' -> {calc_val}. Discrepancy: {margin_error}%.",
                warnings=warnings,
            )
        except Exception as e:
            return CalculationResult(
                is_valid=False,
                calculator_name="safe_math_evaluator",
                expected_value=None,
                actual_value=claimed_result,
                margin_error_pct=100.0,
                explanation=f"Failed to evaluate mathematical expression '{expression}': {str(e)}",
                warnings=[f"Math parse error: {str(e)}"],
            )

