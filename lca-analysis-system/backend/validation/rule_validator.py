"""Rule-based validation for LCA data (Phase 5 from spec)."""

import re
from typing import Any

import structlog

from backend.validation.lca_taxonomy import (
    LIFE_CYCLE_STAGES,
    is_known_category,
    is_recognized_unit,
)

logger = structlog.get_logger(__name__)


# ─── Plausibility ranges (kg CO2-eq per declared unit) ───
PLAUSIBILITY_RANGES: dict[str, tuple[float, float]] = {
    "steel": (1.5, 3.5),
    "concrete": (0.05, 0.3),
    "cement": (0.6, 1.2),
    "aluminium": (8.0, 25.0),
    "aluminum": (8.0, 25.0),
    "copper": (2.0, 10.0),
    "glass": (0.5, 3.0),
    "plastic": (1.5, 6.0),
    "polyethylene": (1.5, 4.0),
    "pvc": (2.0, 6.0),
    "timber": (0.1, 1.0),
    "wood": (0.1, 1.0),
    "paper": (0.5, 2.0),
    "electricity": (0.2, 1.2),  # per kWh
    "natural gas": (2.0, 3.0),  # per m3
    "diesel": (2.5, 4.0),  # per litre
    "transport": (0.01, 0.5),  # per tonne-km
}


class RuleValidationResult:
    """Result of a single rule check."""

    def __init__(
        self,
        rule_name: str,
        passed: bool,
        severity: str = "warning",
        message: str = "",
        details: dict[str, Any] | None = None,
    ):
        self.rule_name = rule_name
        self.passed = passed
        self.severity = severity  # "info", "warning", "error"
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule_name,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


class RuleValidator:
    """Applies deterministic rule-based validation checks to parsed LCA data."""

    # ─── 1. Unit Check ───
    @staticmethod
    def check_units(markdown_content: str) -> list[RuleValidationResult]:
        """Check that units in the content are recognized LCA units."""
        results: list[RuleValidationResult] = []

        # Extract potential unit mentions from table cells and inline
        unit_pattern = re.compile(
            r'\b(kg\s*CO2[\s-]*eq\.?|'
            r't\s*CO2[\s-]*eq\.?|'
            r'g\s*CO2[\s-]*eq\.?|'
            r'mol\s*H\+\s*eq\.?|'
            r'kg\s*SO2[\s-]*eq\.?|'
            r'kg\s*P[\s-]*eq\.?|'
            r'kg\s*N[\s-]*eq\.?|'
            r'kg\s*CFC[\s-]*11\s*eq\.?|'
            r'kg\s*PM2\.5\s*eq\.?|'
            r'kg\s*Sb[\s-]*eq\.?|'
            r'kg\s*NMVOC[\s-]*eq\.?|'
            r'kBq\s*U235\s*eq\.?|'
            r'CTUe|CTUh|'
            r'MJ|GJ|TJ|kWh|'
            r'm[²2][\s·]*(?:year|a)?|m3|'
            r'kg|g|mg|µg|'
            r'disease\s+incidence)',
            re.IGNORECASE,
        )

        found_units = unit_pattern.findall(markdown_content)

        if not found_units:
            results.append(
                RuleValidationResult(
                    rule_name="unit_check",
                    passed=True,
                    severity="info",
                    message="No explicit LCA units detected in content.",
                )
            )
            return results

        unrecognized = []
        for unit in found_units:
            if not is_recognized_unit(unit):
                unrecognized.append(unit)

        if unrecognized:
            results.append(
                RuleValidationResult(
                    rule_name="unit_check",
                    passed=False,
                    severity="warning",
                    message=f"Unrecognized units found: {', '.join(set(unrecognized))}",
                    details={"unrecognized_units": list(set(unrecognized))},
                )
            )
        else:
            results.append(
                RuleValidationResult(
                    rule_name="unit_check",
                    passed=True,
                    severity="info",
                    message=f"All {len(found_units)} detected units are recognized.",
                )
            )

        return results

    # ─── 2. Plausibility Check ───
    @staticmethod
    def check_plausibility(
        markdown_content: str, metadata: dict[str, Any] | None = None
    ) -> list[RuleValidationResult]:
        """Check if numeric values fall within plausible ranges."""
        results: list[RuleValidationResult] = []
        content_lower = markdown_content.lower()

        for material, (low, high) in PLAUSIBILITY_RANGES.items():
            if material in content_lower:
                # Look for numeric values near the material mention
                # Find all numbers within ±200 chars of the material mention
                pattern = re.compile(
                    rf'{re.escape(material)}.{{0,200}}?(\d+[.,]?\d*)',
                    re.IGNORECASE | re.DOTALL,
                )
                matches = pattern.findall(content_lower)

                for match in matches:
                    try:
                        value = float(match.replace(",", "."))
                        if value < low * 0.1 or value > high * 10:
                            results.append(
                                RuleValidationResult(
                                    rule_name="plausibility_check",
                                    passed=False,
                                    severity="warning",
                                    message=(
                                        f"Value {value} for '{material}' is outside "
                                        f"plausible range ({low}-{high} kg CO2-eq)."
                                    ),
                                    details={
                                        "material": material,
                                        "value": value,
                                        "expected_range": [low, high],
                                    },
                                )
                            )
                    except ValueError:
                        continue

        if not results:
            results.append(
                RuleValidationResult(
                    rule_name="plausibility_check",
                    passed=True,
                    severity="info",
                    message="No plausibility issues detected.",
                )
            )

        return results

    # ─── 3. Functional Unit Check ───
    @staticmethod
    def check_functional_unit(markdown_content: str) -> list[RuleValidationResult]:
        """Check if the document declares a functional unit."""
        results: list[RuleValidationResult] = []
        content_lower = markdown_content.lower()

        fu_patterns = [
            r"functional\s+unit",
            r"declared\s+unit",
            r"reference\s+flow",
            r"FU\s*[:=]",
            r"DU\s*[:=]",
        ]

        found = False
        for pat in fu_patterns:
            if re.search(pat, markdown_content, re.IGNORECASE):
                found = True
                break

        if found:
            results.append(
                RuleValidationResult(
                    rule_name="functional_unit_check",
                    passed=True,
                    severity="info",
                    message="Functional/declared unit reference found.",
                )
            )
        else:
            results.append(
                RuleValidationResult(
                    rule_name="functional_unit_check",
                    passed=False,
                    severity="warning",
                    message="No functional unit or declared unit statement detected.",
                )
            )

        return results

    # ─── 4. System Boundary Check ───
    @staticmethod
    def check_system_boundary(markdown_content: str) -> list[RuleValidationResult]:
        """Check if system boundary is declared (A1-C4, cradle-to-gate, etc.)."""
        results: list[RuleValidationResult] = []

        boundary_patterns = [
            r"system\s+boundar",
            r"cradle[\s-]*to[\s-]*gate",
            r"cradle[\s-]*to[\s-]*grave",
            r"gate[\s-]*to[\s-]*gate",
            r"A1[\s-]*[-–][\s-]*A3",
            r"A1[\s-]*[-–][\s-]*C4",
            r"A1[\s-]*[-–][\s-]*D",
        ]

        found = False
        for pat in boundary_patterns:
            if re.search(pat, markdown_content, re.IGNORECASE):
                found = True
                break

        # Also check for life cycle stage codes
        stages_found = []
        for code in LIFE_CYCLE_STAGES:
            if re.search(rf'\b{code}\b', markdown_content):
                stages_found.append(code)

        if found or len(stages_found) >= 3:
            results.append(
                RuleValidationResult(
                    rule_name="system_boundary_check",
                    passed=True,
                    severity="info",
                    message=f"System boundary reference found. Life cycle stages: {stages_found or 'explicit declaration'}",
                    details={"stages_found": stages_found},
                )
            )
        else:
            results.append(
                RuleValidationResult(
                    rule_name="system_boundary_check",
                    passed=False,
                    severity="warning",
                    message="No system boundary declaration detected.",
                    details={"stages_found": stages_found},
                )
            )

        return results

    # ─── 5. Required Sections Check ───
    @staticmethod
    def check_required_sections(markdown_content: str) -> list[RuleValidationResult]:
        """Check if key LCA sections are present (ISO 14040/44)."""
        results: list[RuleValidationResult] = []
        content_lower = markdown_content.lower()

        required_sections = {
            "goal_and_scope": [
                r"goal\s+(and|&)\s+scope",
                r"goal\s+of\s+the\s+study",
                r"scope\s+of\s+the\s+study",
                r"study\s+goal",
            ],
            "inventory_analysis": [
                r"life\s+cycle\s+inventory",
                r"lci\b",
                r"inventory\s+analysis",
                r"inventory\s+data",
            ],
            "impact_assessment": [
                r"life\s+cycle\s+impact\s+assessment",
                r"lcia\b",
                r"impact\s+assessment",
                r"impact\s+categor",
                r"characterization\s+factor",
            ],
            "interpretation": [
                r"interpretation",
                r"sensitivity\s+analysis",
                r"uncertainty\s+analysis",
                r"conclusions?",
                r"recommendations?",
            ],
        }

        missing = []
        found_sections = []

        for section_name, patterns in required_sections.items():
            section_found = False
            for pat in patterns:
                if re.search(pat, markdown_content, re.IGNORECASE):
                    section_found = True
                    break
            if section_found:
                found_sections.append(section_name)
            else:
                missing.append(section_name)

        if missing:
            results.append(
                RuleValidationResult(
                    rule_name="required_sections_check",
                    passed=False,
                    severity="warning",
                    message=f"Missing LCA sections: {', '.join(missing)}",
                    details={
                        "found": found_sections,
                        "missing": missing,
                    },
                )
            )
        else:
            results.append(
                RuleValidationResult(
                    rule_name="required_sections_check",
                    passed=True,
                    severity="info",
                    message="All required LCA sections detected.",
                    details={"found": found_sections},
                )
            )

        return results

    # ─── 6. Impact Category Check ───
    @staticmethod
    def check_impact_categories(markdown_content: str) -> list[RuleValidationResult]:
        """Check if impact categories mentioned are recognized."""
        results: list[RuleValidationResult] = []

        cat_pattern = re.compile(
            r'(climate\s+change|global\s+warming|ozone\s+depletion|'
            r'human\s+toxicity|particulate\s+matter|ionising\s+radiation|'
            r'photochemical\s+ozone|acidification|eutrophication|'
            r'ecotoxicity|land\s+use|water\s+use|water\s+consumption|'
            r'resource\s+use|mineral\s+resource|fossil\s+resource)',
            re.IGNORECASE,
        )

        categories_found = set(m.group().lower() for m in cat_pattern.finditer(markdown_content))

        if categories_found:
            unrecognized = [c for c in categories_found if not is_known_category(c)]
            results.append(
                RuleValidationResult(
                    rule_name="impact_category_check",
                    passed=len(unrecognized) == 0,
                    severity="info" if not unrecognized else "warning",
                    message=f"Found {len(categories_found)} impact categories. Unrecognized: {unrecognized or 'none'}",
                    details={
                        "categories_found": list(categories_found),
                        "unrecognized": unrecognized,
                    },
                )
            )
        else:
            results.append(
                RuleValidationResult(
                    rule_name="impact_category_check",
                    passed=True,
                    severity="info",
                    message="No explicit impact categories detected.",
                )
            )

        return results

    # ─── Run All Rules ───
    def validate(
        self, markdown_content: str, metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Run all rule-based validation checks and return results."""
        all_results: list[RuleValidationResult] = []

        all_results.extend(self.check_units(markdown_content))
        all_results.extend(self.check_plausibility(markdown_content, metadata))
        all_results.extend(self.check_functional_unit(markdown_content))
        all_results.extend(self.check_system_boundary(markdown_content))
        all_results.extend(self.check_required_sections(markdown_content))
        all_results.extend(self.check_impact_categories(markdown_content))

        logger.info(
            "rule_validation_complete",
            total_checks=len(all_results),
            passed=sum(1 for r in all_results if r.passed),
            failed=sum(1 for r in all_results if not r.passed),
        )

        return [r.to_dict() for r in all_results]
