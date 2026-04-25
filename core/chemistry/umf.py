"""Unity Molecular Formula (UMF) calculation engine.

Converts ceramic glaze recipes into their Seger/Unity formula representation,
normalized to flux total = 1.0. Provides surface prediction and limit checking.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .materials import (
    get_material,
    OXIDE_MOLECULAR_WEIGHTS,
    FLUX_OXIDES,
)
from .parser import parse_recipe_string
from .data_loader import load_surface_thresholds, load_umf_targets
from .thermal_expansion import calculate_cte

logger = logging.getLogger(__name__)


# Target formulas (guidelines, not absolute limits)
# Default: cone 10 ranges. Loaded from ceramics-foundation if available.
# Digitalfire notes these are "targets" not "limits" — many successful glazes
# fall outside these ranges. Use as starting points, not rules.
_LIMIT_FORMULAS_DEFAULT: Dict[str, tuple] = {
    "K2O": (0.0, 0.5),
    "Na2O": (0.0, 0.5),
    "KNaO": (0.1, 0.5),  # combined
    "CaO": (0.2, 0.8),
    "MgO": (0.0, 0.4),
    "BaO": (0.0, 0.3),
    "ZnO": (0.0, 0.3),
    "Al2O3": (0.2, 0.6),
    "SiO2": (2.5, 6.0),
    "B2O3": (0.0, 0.3),
}


def get_limit_formulas(cone: int = 10) -> Dict[str, tuple]:
    """Get UMF limit formulas for a specific cone.

    Loads cone-specific ranges from ceramics-foundation if available,
    otherwise falls back to default cone 10 ranges.
    """
    umf_data = load_umf_targets()
    if umf_data and "ranges" in umf_data:
        cone_key = f"cone_{cone}"
        if cone_key in umf_data["ranges"]:
            cone_ranges = umf_data["ranges"][cone_key]
            formulas = {}
            for oxide, bounds in cone_ranges.items():
                if isinstance(bounds, dict) and "min" in bounds and "max" in bounds:
                    formulas[oxide] = (bounds["min"], bounds["max"])
            if formulas:
                return formulas
    return dict(_LIMIT_FORMULAS_DEFAULT)


def _get_surface_thresholds(cone: Optional[int] = None) -> Tuple[float, float]:
    """Get surface prediction thresholds for a given cone.

    Low-fire glazes need more flux to mature, so they appear glossier
    at lower SiO2:Al2O3 ratios than high-fire glazes.

    Returns (t_glossy, t_satin) thresholds.
    """
    data = load_surface_thresholds()
    if data and "cone_thresholds" in data:
        # Find the best matching cone range
        cone_ranges = data["cone_thresholds"]
        if cone is not None:
            # Map cone to range key
            if cone <= 3:
                key = "low_fire"
            elif cone <= 6:
                key = "mid_range"
            elif cone <= 11:
                key = "high_fire"
            else:
                key = "high_fire"
            if key in cone_ranges:
                return (
                    cone_ranges[key].get("glossy", 5),
                    cone_ranges[key].get("satin", 4),
                )

    # Fall back to legacy thresholds or Stull defaults
    if data:
        return (
            data.get("sio2_al2o3_thresholds", {}).get("glossy", 5),
            data.get("sio2_al2o3_thresholds", {}).get("satin", 4),
        )
    return 5, 4


# Legacy name for backward compatibility
LIMIT_FORMULAS = _LIMIT_FORMULAS_DEFAULT


@dataclass
class UMFResult:
    """Result of a UMF calculation."""

    success: bool
    recipe_parsed: bool = False
    umf_formula: Optional[Dict[str, float]] = None
    raw_moles: Optional[Dict[str, float]] = None
    ratios: Dict[str, float] = field(default_factory=dict)
    surface_prediction: Optional[str] = None
    surface_confidence: str = "unknown"
    thermal_expansion: Optional[float] = None
    limit_warnings: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    missing_materials: List[str] = field(default_factory=list)
    cone: Optional[int] = None
    confidence: Dict[str, str] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        result = {
            "success": self.success,
            "recipe_parsed": self.recipe_parsed,
            "umf_formula": self.umf_formula,
            "ratios": self.ratios,
            "surface_prediction": self.surface_prediction,
            "surface_confidence": self.surface_confidence,
            "thermal_expansion": self.thermal_expansion,
            "limit_warnings": self.limit_warnings,
            "warnings": self.warnings,
            "error": self.error,
            "missing_materials": self.missing_materials,
            "cone": self.cone,
            "confidence": self.confidence,
            "recommendations": self.recommendations,
        }
        return result

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return (
            bool(self.limit_warnings)
            or bool(self.warnings)
            or bool(self.missing_materials)
        )


class UMFAnalyzer:
    """Calculate Unity Molecular Formula from glaze recipes."""

    def calculate(self, recipe_string: str, cone: Optional[int] = None) -> UMFResult:
        """Calculate UMF from a recipe string.

        Args:
            recipe_string: Recipe like "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12"
            cone: Target firing cone (e.g., 6, 10). Affects limit checks and surface prediction.

        Returns:
            UMFResult with formula, ratios, surface prediction, CTE, limit warnings,
            confidence indicators, and actionable recommendations.
        """
        effective_cone = cone if cone is not None else 10

        # Step 1: Parse the recipe
        parse_result = parse_recipe_string(recipe_string)

        if not parse_result.success:
            return UMFResult(
                success=False,
                recipe_parsed=False,
                error=f'Could not parse recipe: {"; ".join(parse_result.errors)}',
                warnings=parse_result.errors,
            )

        # Track missing materials for user warning
        missing_materials = []
        for err in parse_result.errors:
            if err.startswith("Unknown material:"):
                mat_name = err.split('"')[1] if '"' in err else err
                missing_materials.append(mat_name)

        # Step 2: Calculate oxide moles from materials
        try:
            moles = self._calculate_moles(parse_result.materials)
        except Exception as e:
            return UMFResult(
                success=False,
                recipe_parsed=True,
                error=f"Mole calculation failed: {e}",
                missing_materials=missing_materials,
            )

        if not moles:
            return UMFResult(
                success=False,
                recipe_parsed=True,
                error="No oxide moles could be calculated",
                missing_materials=missing_materials,
            )

        # Step 3: Normalize to flux sum = 1.0
        umf = self._normalize_to_fluxes(moles)
        if umf is None:
            return UMFResult(
                success=False,
                recipe_parsed=True,
                error="No flux oxides found — cannot normalize to UMF",
                missing_materials=missing_materials,
            )

        # Step 4: Calculate useful ratios
        ratios = self._calculate_ratios(umf)

        # Step 5: Predict surface character (cone-aware)
        surface, surface_confidence = self._predict_surface(ratios, effective_cone)

        # Step 6: Calculate thermal expansion coefficient (ALL oxides, mole fraction method)
        cte = calculate_cte(umf)

        # Step 7: Check against cone-specific limit formulas
        limit_warnings = self._check_limits(umf, effective_cone)

        # Step 8: Build confidence and recommendations
        confidence = self._build_confidence(
            umf, ratios, limit_warnings, surface_confidence, effective_cone
        )
        recommendations = self._build_recommendations(
            umf,
            ratios,
            limit_warnings,
            surface,
            surface_confidence,
            cte,
            effective_cone,
        )

        extra_warnings = []
        if parse_result.normalized:
            extra_warnings.append("Recipe percentages were normalized to sum to 100")

        if missing_materials:
            return UMFResult(
                success=False,
                recipe_parsed=True,
                umf_formula=umf,
                raw_moles=moles,
                ratios=ratios,
                surface_prediction=surface,
                surface_confidence=surface_confidence,
                thermal_expansion=cte,
                limit_warnings=limit_warnings,
                warnings=extra_warnings,
                missing_materials=missing_materials,
                cone=effective_cone,
                confidence=confidence,
                recommendations=[
                    f'Materials not found in database: {", ".join(missing_materials)}.',
                    "The UMF shown is INCOMPLETE — missing materials were excluded.",
                    "Try these alternative names, or check the materials database.",
                ],
                error=f'Unknown materials: {", ".join(missing_materials)}',
            )

        return UMFResult(
            success=True,
            recipe_parsed=True,
            umf_formula=umf,
            raw_moles=moles,
            ratios=ratios,
            surface_prediction=surface,
            surface_confidence=surface_confidence,
            thermal_expansion=cte,
            limit_warnings=limit_warnings,
            warnings=extra_warnings,
            missing_materials=missing_materials,
            cone=effective_cone,
            confidence=confidence,
            recommendations=recommendations,
        )

    def _calculate_moles(self, materials: Dict[str, float]) -> Dict[str, float]:
        """Convert materials to oxide molar amounts.

        For each material: apply LOI, compute oxide mass contribution,
        divide by molecular weight to get moles.
        """
        moles: Dict[str, float] = {}

        for material_name, amount in materials.items():
            material = get_material(material_name)
            if material is None:
                logger.warning(f"Material not found during mole calc: {material_name}")
                continue

            # Effective amount after LOI
            effective_amount = amount * (1.0 - material.loi / 100.0)

            for oxide, percentage in material.oxides.items():
                if oxide not in OXIDE_MOLECULAR_WEIGHTS:
                    logger.debug(f"No molecular weight for oxide: {oxide}")
                    continue

                oxide_mass = effective_amount * (percentage / 100.0)
                oxide_moles = oxide_mass / OXIDE_MOLECULAR_WEIGHTS[oxide]

                moles[oxide] = moles.get(oxide, 0.0) + oxide_moles

        return moles

    def _normalize_to_fluxes(
        self, moles: Dict[str, float]
    ) -> Optional[Dict[str, float]]:
        """Normalize oxide moles so flux total = 1.0.

        Returns None if no flux oxides are present.
        """
        flux_total = 0.0
        for oxide in FLUX_OXIDES:
            flux_total += moles.get(oxide, 0.0)

        if flux_total == 0:
            return None

        normalized = {}
        for oxide, value in moles.items():
            normalized[oxide] = round(value / flux_total, 4)

        return normalized

    def _calculate_ratios(self, umf: Dict[str, float]) -> Dict[str, float]:
        """Calculate useful ratios from the UMF formula."""
        ratios = {}

        sio2 = umf.get("SiO2", 0)
        al2o3 = umf.get("Al2O3", 0)
        cao = umf.get("CaO", 0)
        k2o = umf.get("K2O", 0)
        na2o = umf.get("Na2O", 0)

        # SiO2:Al2O3 ratio (the most important in glaze chemistry)
        if al2o3 > 0:
            ratios["sio2_al2o3"] = round(sio2 / al2o3, 2)
        else:
            ratios["sio2_al2o3"] = 0.0

        # Flux:Al2O3 ratio
        if al2o3 > 0:
            ratios["flux_al2o3"] = round(1.0 / al2o3, 2)  # flux sum is always 1.0
        else:
            ratios["flux_al2o3"] = 0.0

        # KNaO:CaO ratio
        knao = k2o + na2o
        if cao > 0:
            ratios["knao_cao"] = round(knao / cao, 2)
        else:
            ratios["knao_cao"] = 0.0 if knao == 0 else 99.0

        # Total flux diversity
        flux_count = sum(1 for ox in FLUX_OXIDES if umf.get(ox, 0) > 0.01)
        ratios["flux_diversity"] = flux_count

        # Alumina:Silica ratio (inverse, useful for mattness)
        if sio2 > 0:
            ratios["al2o3_sio2"] = round(al2o3 / sio2, 3)

        return ratios

    def _predict_surface(self, ratios: Dict[str, float], cone: int) -> Tuple[str, str]:
        """Predict surface character from UMF ratios.

        Uses cone-specific thresholds. Low-fire glazes mature with more flux,
        so they tend to be glossier at lower SiO2:Al2O3 ratios.

        Returns (surface, confidence) where confidence is 'high', 'medium', or 'low'
        based on distance from the nearest threshold.
        """
        sio2_al2o3 = ratios.get("sio2_al2o3", 0)

        t_glossy, t_satin = _get_surface_thresholds(cone)

        # Determine surface
        if sio2_al2o3 >= t_glossy:
            surface = "glossy"
            boundary = t_glossy
        elif sio2_al2o3 >= t_satin:
            surface = "satin"
            lower_boundary = t_satin
            upper_boundary = t_glossy
            # Distance to nearest boundary
            dist_to_lower = sio2_al2o3 - lower_boundary
            dist_to_upper = upper_boundary - sio2_al2o3
            boundary = (
                lower_boundary if dist_to_lower < dist_to_upper else upper_boundary
            )
        elif sio2_al2o3 > 0:
            surface = "matte"
            boundary = t_satin
        else:
            surface = "dry_underfired"
            boundary = t_satin

        # Confidence based on distance from nearest boundary
        if surface == "dry_underfired":
            confidence = "low"
        else:
            distance = abs(sio2_al2o3 - boundary)
            if distance >= 0.3:
                confidence = "high"
            elif distance >= 0.1:
                confidence = "medium"
            else:
                confidence = "low"

        return surface, confidence

    def _check_limits(self, umf: Dict[str, float], cone: int) -> List[str]:
        """Check UMF values against cone-specific target formula guidelines.

        Note: these are guidelines based on common ranges for the target cone,
        not absolute limits. Many successful glazes fall outside these ranges.
        """
        warnings = []
        limit_formulas = get_limit_formulas(cone)

        # Check individual oxides
        for oxide, (lo, hi) in limit_formulas.items():
            if oxide == "KNaO":
                # Combined alkali check
                value = umf.get("K2O", 0) + umf.get("Na2O", 0)
            else:
                value = umf.get(oxide, 0)

            if value > 0 and value < lo:
                warnings.append(
                    f"{oxide} ({value:.2f}) is below the typical cone {cone} range ({lo}-{hi}). Many glazes work outside these guidelines — this is informational only."
                )
            elif value > hi:
                warnings.append(
                    f"{oxide} ({value:.2f}) is above the typical cone {cone} range ({lo}-{hi}). Many classic glazes intentionally exceed these ranges — this is informational only."
                )

        # Additional practical checks (cone-aware)
        sio2 = umf.get("SiO2", 0)
        si_max = limit_formulas.get("SiO2", (0, 6.0))[1]
        if sio2 > si_max:
            warnings.append(
                f"SiO₂ ({sio2:.2f}) is above typical. High-silica glazes are common in ash glazes and some traditional formulations. Firing test required."
            )

        al2o3 = umf.get("Al2O3", 0)
        al_max = limit_formulas.get("Al2O3", (0, 0.6))[1]
        if al2o3 > al_max:
            warnings.append(
                f"Al₂O₃ ({al2o3:.2f}) is above typical. High-alumina glazes like Shino intentionally use this range. Firing test required."
            )

        b2o3 = umf.get("B2O3", 0)
        b_max = limit_formulas.get("B2O3", (0, 0.3))[1]
        if b2o3 > b_max:
            warnings.append(
                f"B₂O₃ ({b2o3:.2f}) is above typical. High-boron glazes melt at lower temperatures but may be fluid. Firing test required."
            )

        return warnings

    def _build_confidence(
        self,
        umf: Dict[str, float],
        ratios: Dict[str, float],
        limit_warnings: List[str],
        surface_confidence: str,
        cone: int,
    ) -> Dict[str, str]:
        """Build confidence indicators for each prediction."""
        confidence = {
            "surface": surface_confidence,
        }

        # Limit confidence
        if not limit_warnings:
            confidence["limits"] = "high"
        else:
            # Count how many are "near edge" vs "far outside"
            near_edge = 0
            far_outside = 0
            for w in limit_warnings:
                # Parse the warning to see how far outside
                # Format: "OXIDE (X.XX) is below/above typical range (LO-HI)"
                try:
                    parts = w.split()
                    value_str = parts[1].strip("()")
                    value = float(value_str)
                    range_str = parts[-2].strip("— guideline only").strip()
                    lo, hi = map(float, range_str.split("-"))
                    if value < lo:
                        deviation = (lo - value) / lo if lo > 0 else 0
                    else:
                        deviation = (value - hi) / hi if hi > 0 else 0
                    if deviation <= 0.2:
                        near_edge += 1
                    else:
                        far_outside += 1
                except (ValueError, IndexError):
                    near_edge += 1

            if far_outside > 0:
                confidence["limits"] = "low"
            elif near_edge > 0:
                confidence["limits"] = "medium"
            else:
                confidence["limits"] = "high"

        # Overall confidence
        levels = {"high": 3, "medium": 2, "low": 1, "unknown": 0}
        surface_lvl = levels.get(surface_confidence, 0)
        limit_lvl = levels.get(confidence.get("limits", "unknown"), 0)
        overall = min(surface_lvl, limit_lvl)
        confidence["overall"] = {3: "high", 2: "medium", 1: "low", 0: "unknown"}[
            overall
        ]

        return confidence

    def _build_recommendations(
        self,
        umf: Dict[str, float],
        ratios: Dict[str, float],
        limit_warnings: List[str],
        surface: str,
        surface_confidence: str,
        cte: Optional[float],
        cone: int,
    ) -> List[str]:
        """Build actionable recommendations based on the analysis."""
        recommendations = []
        sio2_al2o3 = ratios.get("sio2_al2o3", 0)

        # Surface confidence recommendation
        if surface_confidence == "low":
            if surface == "matte":
                recommendations.append(
                    f"This glaze is near the matte/satin boundary (SiO₂:Al₂O₃ = {sio2_al2o3:.2f}). "
                    f"Fire a test tile at cone {cone} to confirm surface character."
                )
            elif surface == "satin":
                recommendations.append(
                    f"This glaze is near a surface boundary (SiO₂:Al₂O₃ = {sio2_al2o3:.2f}). "
                    f"Small changes in application thickness or cooling rate may shift the result."
                )
            elif surface == "glossy":
                recommendations.append(
                    f"This glaze is near the satin/glossy boundary (SiO₂:Al₂O₃ = {sio2_al2o3:.2f}). "
                    f"Slow cooling may increase gloss; fast cooling may produce satin."
                )

        # Limit-based recommendations
        for warning in limit_warnings:
            if "SiO2" in warning and "below" in warning:
                recommendations.append(
                    f"SiO₂ is below typical for cone {cone}. If the glaze is too fluid, "
                    f"try adding 5-10% silica. If it works as-is, the guideline does not apply to your formulation."
                )
            elif "SiO2" in warning and "above" in warning:
                recommendations.append(
                    f"SiO₂ is above typical for cone {cone}. High-silica glazes can be excellent — "
                    f"fire a test tile to check maturity."
                )
            elif "Al2O3" in warning and "below" in warning:
                recommendations.append(
                    "Al₂O₃ is below typical. If the glaze runs, try adding 2-5% kaolin. "
                    "Low-alumina glazes can produce interesting fluid effects."
                )
            elif "Al2O3" in warning and "above" in warning:
                recommendations.append(
                    "Al₂O₃ is above typical. This is characteristic of high-alumina glazes like Shino. "
                    "Fire a test tile to confirm surface and maturity."
                )
            elif "B2O3" in warning and "above" in warning:
                recommendations.append(
                    "B₂O₃ is above typical. Boron lowers melting point — this may be intentional for low-fire glazes. "
                    "Apply thinly and use a catch plate for testing."
                )
            elif "KNaO" in warning and "above" in warning:
                recommendations.append(
                    "Alkali content is above typical. High-alkali glazes can craze on some clay bodies. "
                    "Test on your clay body before using on functional ware."
                )

        # CTE-based recommendations
        if cte is not None:
            if cte > 7.5:
                recommendations.append(
                    f"High thermal expansion (CTE = {cte:.1f}×10⁻⁶/°C) suggests crazing risk "
                    f"on low-expansion bodies. Test on your clay body before committing."
                )
            elif cte < 5.5:
                recommendations.append(
                    f"Low thermal expansion (CTE = {cte:.1f}×10⁻⁶/°C) suggests shivering risk "
                    f"on high-expansion bodies. Test on your clay body before committing."
                )

        # Mandatory test-tile recommendation for ALL results
        recommendations.append(
            f"Fire a test tile at cone {cone} on your clay body to confirm surface, "
            f"color, and fit. UMF analysis predicts chemistry but cannot replace firing tests."
        )

        # Literature references
        recommendations.append(
            "References: Stull chart (Stull 1912) for SiO₂:Al₂O₃ surface prediction; "
            "Appen molar coefficients for thermal expansion; Schermann limit formulas for UMF targets."
        )

        return recommendations


# Module-level convenience function
_analyzer = UMFAnalyzer()


def calculate_umf(recipe: str, cone: Optional[int] = None) -> UMFResult:
    """Calculate UMF from a recipe string using the default analyzer.

    Args:
        recipe: Recipe string like "Feldspar 45, Silica 30, Whiting 15, Kaolin 10"
        cone: Target firing cone. Defaults to 10.
    """
    return _analyzer.calculate(recipe, cone=cone)
