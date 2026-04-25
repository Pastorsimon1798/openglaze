"""Layering compatibility analysis for ceramic glaze combinations.

Analyzes whether two glazes are compatible when layered, using physically-based
scoring weighted by actual ceramic engineering factors:

  - Thermal expansion match (40%): Most critical for fit
  - Fluidity match (25%): Affects crawling/running
  - Oxide interactions (20%): Chemical incompatibilities
  - Maturing similarity (15%): Both should mature at target cone

CTE is calculated using the molar method (Appen/Sankey) with ALL oxides.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .umf import UMFResult, calculate_umf
from .thermal_expansion import calculate_cte
from .data_loader import load_layering_rules

logger = logging.getLogger(__name__)


@dataclass
class CompatibilityResult:
    """Result of compatibility analysis between two glazes."""

    success: bool
    compatible: bool = False
    score: float = 0.0  # 0-1, higher = more compatible
    risk_factors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommended_order: Optional[str] = None
    thermal_expansion_risk: str = "unknown"
    thermal_expansion_delta: Optional[float] = None
    cte_base: Optional[float] = None
    cte_top: Optional[float] = None
    fluidity_interaction: str = "unknown"
    oxide_interactions: List[str] = field(default_factory=list)
    base_umf: Optional[UMFResult] = None
    top_umf: Optional[UMFResult] = None
    cone: Optional[int] = None
    test_recommendations: List[str] = field(default_factory=list)
    risk_breakdown: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "success": self.success,
            "compatible": self.compatible,
            "score": self.score,
            "risk_factors": self.risk_factors,
            "warnings": self.warnings,
            "recommended_order": self.recommended_order,
            "thermal_expansion_risk": self.thermal_expansion_risk,
            "thermal_expansion_delta": self.thermal_expansion_delta,
            "cte_base": self.cte_base,
            "cte_top": self.cte_top,
            "fluidity_interaction": self.fluidity_interaction,
            "oxide_interactions": self.oxide_interactions,
            "base_umf": self.base_umf.to_dict() if self.base_umf else None,
            "top_umf": self.top_umf.to_dict() if self.top_umf else None,
            "cone": self.cone,
            "test_recommendations": self.test_recommendations,
            "risk_breakdown": self.risk_breakdown,
        }


# Shino glaze names (for the hard shino-over-non-shino rule)
_SHINO_NAMES_DEFAULT = {"shino", "luster shino", "malcom's shino", "malcoms shino"}

# Load canonical layering rules from ceramics-foundation if available
_LAYERING_RULES = load_layering_rules()
if _LAYERING_RULES and "shino_crawl_risk" in _LAYERING_RULES:
    _SHINO_NAMES = set(_LAYERING_RULES["shino_crawl_risk"]["shino_names"])
else:
    _SHINO_NAMES = _SHINO_NAMES_DEFAULT


class CompatibilityAnalyzer:
    """Analyze layering compatibility between two glazes using physically-based scoring."""

    # Scoring weights (must sum to 1.0)
    WEIGHT_THERMAL = 0.40
    WEIGHT_FLUIDITY = 0.25
    WEIGHT_OXIDE = 0.20
    WEIGHT_MATURING = 0.15

    def analyze(
        self,
        base_recipe: Optional[str],
        top_recipe: Optional[str],
        base_name: str = "",
        top_name: str = "",
        cone: Optional[int] = None,
    ) -> CompatibilityResult:
        """Analyze compatibility between base and top glaze recipes.

        Args:
            base_recipe: Recipe string for the base glaze (applied first).
            top_recipe: Recipe string for the top glaze (applied last).
            base_name: Name of the base glaze.
            top_name: Name of the top glaze.
            cone: Target firing cone for the combination.

        Returns:
            CompatibilityResult with physically-based score, recommendations,
            and specific "what to test" guidance.
        """
        base_name_lower = base_name.lower().strip()
        top_name_lower = top_name.lower().strip()
        effective_cone = cone if cone is not None else 10

        # Hard rules first — these override everything
        shino_result = self._shino_check(top_name_lower, base_name_lower)
        if shino_result:
            return CompatibilityResult(
                success=True,
                compatible=False,
                score=0.0,
                risk_factors=[shino_result],
                warnings=[
                    "High crawl risk — Shino over non-Shino frequently crawls due to different thermal expansion."
                ],
                recommended_order=(
                    f"{base_name} over {top_name}"
                    if self._is_shino(base_name_lower)
                    else None
                ),
                thermal_expansion_risk="high",
                fluidity_interaction="crawl_likely",
                oxide_interactions=[],
                cone=effective_cone,
                test_recommendations=[
                    "Reverse the layer order: apply Shino as the base layer.",
                    "If keeping this order, apply Shino VERY thinly (1 coat) over a fully-dry base.",
                    "Fire a vertical test tile first — Shino over non-Shino often crawls.",
                ],
                risk_breakdown=[
                    {
                        "risk": "shino_crawl",
                        "severity": "critical",
                        "mitigation": "Reverse layer order or apply Shino as a very thin single coat",
                    }
                ],
            )

        # Calculate UMF for both glazes (cone-aware)
        base_umf = (
            calculate_umf(base_recipe, cone=effective_cone) if base_recipe else None
        )
        top_umf = calculate_umf(top_recipe, cone=effective_cone) if top_recipe else None

        risk_factors = []
        warnings = []
        oxide_interactions = []

        # If either recipe can't be parsed, return limited result
        if base_umf is None or not base_umf.success:
            if top_umf is None or not top_umf.success:
                return CompatibilityResult(
                    success=False,
                    compatible=None,
                    score=0.5,
                    warnings=[
                        "Neither glaze has a parseable recipe — limited analysis"
                    ],
                    base_umf=base_umf,
                    top_umf=top_umf,
                    cone=effective_cone,
                    test_recommendations=[
                        "Add recipe data for both glazes to get a full compatibility analysis.",
                    ],
                )
            warnings.append("Base glaze recipe not parseable — limited analysis")

        if top_umf is None or not top_umf.success:
            warnings.append("Top glaze recipe not parseable — limited analysis")

        # Only do full analysis if both UMFs are available
        if base_umf and base_umf.success and top_umf and top_umf.success:
            # 1. Thermal expansion check (40% weight)
            cte_base = calculate_cte(base_umf.umf_formula)
            cte_top = calculate_cte(top_umf.umf_formula)
            thermal_score, thermal_risk, thermal_mismatch, thermal_desc = (
                self._score_thermal(cte_base, cte_top)
            )
            if thermal_risk == "high":
                risk_factors.append(thermal_desc)
            elif thermal_risk == "medium":
                warnings.append(thermal_desc)

            # 2. Fluidity interaction check (25% weight)
            fluidity_score, fluidity, fluidity_desc = self._score_fluidity(
                base_umf, top_umf
            )
            if "crawl" in fluidity.lower() or "run" in fluidity.lower():
                risk_factors.append(fluidity_desc)
            elif "moderate" in fluidity.lower():
                warnings.append(fluidity_desc)

            # 3. Oxide interaction check (20% weight)
            oxide_interactions = self._oxide_interactions(
                base_umf, top_umf, base_name_lower, top_name_lower
            )
            oxide_score = self._score_oxides(oxide_interactions)
            for interaction in oxide_interactions:
                if any(
                    word in interaction.lower()
                    for word in ["kill", "destroy", "critical", "suppress"]
                ):
                    risk_factors.append(interaction)
                elif any(
                    word in interaction.lower()
                    for word in ["may", "could", "risk", "migrate"]
                ):
                    warnings.append(interaction)

            # 4. Maturing similarity (15% weight)
            maturing_score = self._score_maturing(base_umf, top_umf)

            # Calculate overall weighted score
            score = (
                thermal_score * self.WEIGHT_THERMAL
                + fluidity_score * self.WEIGHT_FLUIDITY
                + oxide_score * self.WEIGHT_OXIDE
                + maturing_score * self.WEIGHT_MATURING
            )

            # Build test recommendations and risk breakdown
            test_recommendations = self._build_test_recommendations(
                base_umf,
                top_umf,
                thermal_risk,
                thermal_mismatch,
                fluidity,
                oxide_interactions,
                score,
                effective_cone,
            )
            risk_breakdown = self._build_risk_breakdown(
                cte_base,
                cte_top,
                thermal_risk,
                thermal_mismatch,
                fluidity,
                oxide_interactions,
                effective_cone,
            )

            return CompatibilityResult(
                success=True,
                compatible=score >= 0.5,
                score=round(score, 2),
                risk_factors=risk_factors,
                warnings=warnings,
                recommended_order=None,
                thermal_expansion_risk=thermal_risk,
                thermal_expansion_delta=thermal_mismatch,
                cte_base=cte_base,
                cte_top=cte_top,
                fluidity_interaction=fluidity,
                oxide_interactions=oxide_interactions,
                base_umf=base_umf,
                top_umf=top_umf,
                cone=effective_cone,
                test_recommendations=test_recommendations,
                risk_breakdown=risk_breakdown,
            )

        # Partial analysis (one or both recipes missing)
        score = 0.5 if not risk_factors else max(0.0, 0.5 - len(risk_factors) * 0.2)
        return CompatibilityResult(
            success=True,
            compatible=score >= 0.5,
            score=round(score, 2),
            risk_factors=risk_factors,
            warnings=warnings,
            base_umf=base_umf,
            top_umf=top_umf,
            cone=effective_cone,
            test_recommendations=[
                "Add complete recipe data for both glazes to get full compatibility analysis.",
            ],
        )

    def _build_test_recommendations(
        self,
        base_umf: UMFResult,
        top_umf: UMFResult,
        thermal_risk: str,
        thermal_mismatch: Optional[float],
        fluidity: str,
        oxide_interactions: List[str],
        score: float,
        cone: int,
    ) -> List[str]:
        """Build specific, actionable testing recommendations."""
        recommendations = []

        # Score-based overall recommendation
        if score >= 0.8:
            recommendations.append(
                f"High compatibility score ({score:.2f}). This combination looks promising. "
                f"Fire a test tile at cone {cone} to confirm color and surface."
            )
        elif score >= 0.5:
            recommendations.append(
                f"Moderate compatibility ({score:.2f}). Test carefully before using on important work."
            )
        else:
            recommendations.append(
                f"Low compatibility score ({score:.2f}). Expect problems. Consider reformulating or choosing a different combination."
            )

        # Thermal recommendations
        if thermal_risk == "high" and thermal_mismatch is not None:
            abs_mismatch = abs(thermal_mismatch)
            if thermal_mismatch > 0:
                # Top expands more
                recommendations.append(
                    "Top glaze has higher CTE (expands more when heated). Crazing risk on cooling. "
                    "Test on your clay body. If crazing occurs: add 5-10% silica to the top glaze, "
                    "or replace some feldspar with clay."
                )
            else:
                # Base expands more
                recommendations.append(
                    "Base glaze has higher CTE (expands more when heated). Shivering risk on cooling. "
                    "Test on your clay body. If shivering occurs: add 2-5% nepheline syenite to the base, "
                    "or reduce silica in the top glaze."
                )
            recommendations.append(
                f"CTE difference of {abs_mismatch:.1f}×10⁻⁶/°C is significant. "
                f"Fire a test tile and examine for cracks after 24 hours (some crazing appears after cooling)."
            )
        elif thermal_risk == "medium":
            recommendations.append(
                "Moderate thermal mismatch. Fire a test tile and check for crazing/shivering "
                "after the piece has fully cooled (wait 24 hours)."
            )

        # Fluidity recommendations
        if "run" in fluidity.lower():
            recommendations.append(
                "Top glaze is more fluid than base — running risk at edges and drips. "
                "Apply top glaze thinly (2 coats max). Test on a vertical tile first. "
                "Use a catch plate or kiln wash under test pieces."
            )
        elif "crawl" in fluidity.lower():
            recommendations.append(
                "Top glaze is stiffer than base — crawling risk at thin spots. "
                "Apply base glaze thickly (3-4 coats), top glaze medium (2-3 coats). "
                "Ensure base is fully dry before applying top. Test on flat tile first."
            )
        elif "moderate" in fluidity.lower():
            recommendations.append(
                "Moderate fluidity difference. Standard application (2-3 coats each) should work. "
                "Monitor edges on vertical test tile."
            )

        # Oxide interaction recommendations
        for interaction in oxide_interactions:
            if "suppresses copper red" in interaction.lower():
                recommendations.append(
                    "Iron in one layer suppresses copper red in the other. "
                    "If you want red: use an iron-free base, or move copper to the base layer. "
                    "If you want a different effect: this may produce interesting browns/greens."
                )
            elif "zinc destroys pink" in interaction.lower():
                recommendations.append(
                    "Zinc destroys chrome-tin pink. Remove zinc from one layer, "
                    "or accept that pink will not develop."
                )
            elif "very high combined iron" in interaction.lower():
                recommendations.append(
                    "High combined iron may produce very dark/muddy results. "
                    "Consider reducing iron in one layer, or embrace the tenmoku-like darkness."
                )
            elif "chromium" in interaction.lower():
                recommendations.append(
                    "Chromium can volatilize and discolor nearby pieces. "
                    "Place test tile away from other work in the kiln. Use ventilation."
                )

        # Cone recommendation
        recommendations.append(
            f"Fire test tile to cone {cone} with your standard schedule. "
            f"Use witness cones to verify actual temperature."
        )

        return recommendations

    def _build_risk_breakdown(
        self,
        cte_base: Optional[float],
        cte_top: Optional[float],
        thermal_risk: str,
        thermal_mismatch: Optional[float],
        fluidity: str,
        oxide_interactions: List[str],
        cone: int,
    ) -> List[Dict[str, str]]:
        """Build structured risk breakdown with severity and mitigation."""
        breakdown = []

        # Thermal risk
        if thermal_risk != "unknown" and thermal_mismatch is not None:
            abs_mismatch = abs(thermal_mismatch)
            if abs_mismatch < 0.5:
                severity = "low"
            elif abs_mismatch < 1.5:
                severity = "medium"
            else:
                severity = "high"

            if thermal_mismatch > 0:
                mitigation = (
                    f"Add 5-10% silica to top glaze, or reduce alkali fluxes. "
                    f"Test on your clay body at cone {cone}."
                )
            else:
                mitigation = (
                    f"Add 2-5% nepheline syenite to base glaze, or reduce silica in top. "
                    f"Test on your clay body at cone {cone}."
                )

            breakdown.append(
                {
                    "risk": "thermal_expansion_mismatch",
                    "severity": severity,
                    "detail": f"CTE delta: {thermal_mismatch:+.2f}×10⁻⁶/°C (base: {cte_base}, top: {cte_top})",
                    "mitigation": mitigation,
                }
            )

        # Fluidity risk
        if "run" in fluidity.lower():
            breakdown.append(
                {
                    "risk": "running",
                    "severity": "high" if "severe" in fluidity.lower() else "medium",
                    "detail": fluidity,
                    "mitigation": "Apply top glaze thinly (2 coats). Test on vertical tile. Use catch plate.",
                }
            )
        elif "crawl" in fluidity.lower():
            breakdown.append(
                {
                    "risk": "crawling",
                    "severity": "high" if "severe" in fluidity.lower() else "medium",
                    "detail": fluidity,
                    "mitigation": "Apply base thickly, ensure fully dry before top coat. Test on flat tile first.",
                }
            )

        # Oxide risks
        for interaction in oxide_interactions:
            if "suppresses copper red" in interaction.lower():
                breakdown.append(
                    {
                        "risk": "color_suppression",
                        "severity": "high",
                        "detail": interaction,
                        "mitigation": "Use iron-free base for copper red, or accept brown/green result.",
                    }
                )
            elif "zinc destroys pink" in interaction.lower():
                breakdown.append(
                    {
                        "risk": "color_suppression",
                        "severity": "critical",
                        "detail": interaction,
                        "mitigation": "Remove zinc from one layer. Zinc and chrome-tin pink are incompatible.",
                    }
                )
            elif "critical" in interaction.lower() and "iron" in interaction.lower():
                breakdown.append(
                    {
                        "risk": "muddy_result",
                        "severity": "medium",
                        "detail": interaction,
                        "mitigation": "Reduce iron in one layer, or embrace the dark tenmoku-like result.",
                    }
                )
            elif "chromium" in interaction.lower():
                breakdown.append(
                    {
                        "risk": "kiln_contamination",
                        "severity": "medium",
                        "detail": interaction,
                        "mitigation": "Isolate test piece from other work. Use ventilation.",
                    }
                )

        return breakdown

    def _is_shino(self, name: str) -> bool:
        """Check if a glaze name indicates a shino."""
        name_clean = name.lower().strip()
        return name_clean in _SHINO_NAMES or "shino" in name_clean

    def _shino_check(self, top_name: str, base_name: str) -> Optional[str]:
        """Shino over non-shino has high crawl risk due to different thermal expansion."""
        if self._is_shino(top_name) and not self._is_shino(base_name):
            return f"SHINO OVER NON-SHINO: {top_name} over {base_name} has high crawl risk. Consider reversing the layer order or applying very thin."
        return None

    def _score_thermal(
        self, cte_base: Optional[float], cte_top: Optional[float]
    ) -> tuple:
        """Score thermal expansion compatibility.

        Returns: (score, risk_level, mismatch_value, description)
        """
        if cte_base is None or cte_top is None:
            return (
                0.5,
                "unknown",
                None,
                "CTE could not be calculated for one or both glazes",
            )

        mismatch = round(cte_top - cte_base, 2)
        abs_mismatch = abs(mismatch)

        if abs_mismatch < 0.5:
            score = 1.0
            risk = "low"
            desc = f"Excellent thermal match (ΔCTE {mismatch:+.2f} ×10⁻⁶/°C)"
        elif abs_mismatch < 1.0:
            score = 0.7
            risk = "low"
            desc = (
                f"Good thermal match (ΔCTE {mismatch:+.2f} ×10⁻⁶/°C) — test recommended"
            )
        elif abs_mismatch < 1.5:
            score = 0.4
            risk = "medium"
            desc = f"Moderate thermal mismatch (ΔCTE {mismatch:+.2f} ×10⁻⁶/°C) — tile test essential"
        elif abs_mismatch < 2.5:
            score = 0.2
            risk = "high"
            if mismatch > 0:
                desc = f"High mismatch (ΔCTE {mismatch:+.2f} ×10⁻⁶/°C) — top expands more. Crazing risk."
            else:
                desc = f"High mismatch (ΔCTE {mismatch:+.2f} ×10⁻⁶/°C) — base expands more. Shivering risk."
        else:
            score = 0.0
            risk = "high"
            if mismatch > 0:
                desc = f"Severe mismatch (ΔCTE {mismatch:+.2f} ×10⁻⁶/°C) — top glaze will likely craze or peel"
            else:
                desc = f"Severe mismatch (ΔCTE {mismatch:+.2f} ×10⁻⁶/°C) — top glaze will likely shiver or flake"

        return score, risk, mismatch, desc

    def _score_fluidity(self, base_umf: UMFResult, top_umf: UMFResult) -> tuple:
        """Score fluidity interaction.

        Returns: (score, fluidity_label, description)
        """
        base_ratio = base_umf.ratios.get("sio2_al2o3", 3.0)
        top_ratio = top_umf.ratios.get("sio2_al2o3", 3.0)
        delta = abs(top_ratio - base_ratio)

        if delta < 1.0:
            score = 1.0
            label = f"Similar fluidity (base {base_ratio:.1f}, top {top_ratio:.1f}) — good interaction"
            desc = label
        elif delta < 2.0:
            score = 0.7
            label = f"Moderate fluidity difference (base {base_ratio:.1f}, top {top_ratio:.1f}) — acceptable"
            desc = label
        elif delta < 3.5:
            score = 0.4
            if top_ratio > base_ratio:
                label = f"Top stiffer than base (Δ{delta:.1f}) — potential crawling at thin spots"
                desc = label
            else:
                label = (
                    f"Top more fluid than base (Δ{delta:.1f}) — running risk at edges"
                )
                desc = label
        else:
            score = 0.1
            if top_ratio > base_ratio:
                label = f"Severe: top much stiffer than base (Δ{delta:.1f}) — high crawl risk"
                desc = label
            else:
                label = f"Severe: top much more fluid than base (Δ{delta:.1f}) — high run risk"
                desc = label

        return score, label, desc

    def _score_oxides(self, interactions: List[str]) -> float:
        """Score oxide interaction risk.

        Critical interactions (kill/destroy) = 0.0
        Warning interactions (may/could) = 0.5
        No interactions = 1.0
        """
        if not interactions:
            return 1.0

        critical = sum(
            1
            for i in interactions
            if any(w in i.lower() for w in ["kill", "destroy", "critical", "suppress"])
        )
        warnings = sum(
            1
            for i in interactions
            if any(w in i.lower() for w in ["may", "could", "risk", "migrate"])
        )

        score = 1.0 - (critical * 0.4) - (warnings * 0.15)
        return max(0.0, min(1.0, score))

    def _score_maturing(self, base_umf: UMFResult, top_umf: UMFResult) -> float:
        """Score maturing temperature similarity.

        Uses Al2O3 as a proxy — high alumina glazes typically mature at higher temps.
        This is a rough heuristic; true maturing temp requires full firing data.
        """
        base_al = base_umf.umf_formula.get("Al2O3", 0.4)
        top_al = top_umf.umf_formula.get("Al2O3", 0.4)
        delta = abs(base_al - top_al)

        if delta < 0.1:
            return 1.0
        elif delta < 0.2:
            return 0.7
        elif delta < 0.35:
            return 0.4
        else:
            return 0.2

    def _oxide_interactions(
        self, base_umf: UMFResult, top_umf: UMFResult, base_name: str, top_name: str
    ) -> List[str]:
        """Check for problematic oxide interactions between layers."""
        interactions = []
        base_oxides = base_umf.umf_formula or {}
        top_oxides = top_umf.umf_formula or {}

        base_fe = base_oxides.get("Fe2O3", 0)
        top_fe = top_oxides.get("Fe2O3", 0)
        base_cu = base_oxides.get("CuO", 0)
        top_cu = top_oxides.get("CuO", 0)
        base_co = base_oxides.get("CoO", 0)
        top_co = top_oxides.get("CoO", 0)
        base_mn = base_oxides.get("MnO", 0)
        top_mn = top_oxides.get("MnO", 0)
        base_zn = base_oxides.get("ZnO", 0)
        top_zn = top_oxides.get("ZnO", 0)
        base_sn = base_oxides.get("SnO2", 0)
        top_sn = top_oxides.get("SnO2", 0)
        base_cr = base_oxides.get("Cr2O3", 0)
        top_cr = top_oxides.get("Cr2O3", 0)

        # Iron suppresses copper red
        if base_fe > 0.05 and top_cu > 0.01:
            interactions.append(
                "Iron in base layer suppresses copper red development in top layer"
            )
        if top_fe > 0.05 and base_cu > 0.01:
            interactions.append(
                "Iron in top layer may muddy copper colors in base layer"
            )

        # Zinc kills chrome-tin pink
        if (base_sn > 0.02 or top_sn > 0.02) and (base_cr > 0.001 or top_cr > 0.001):
            if base_zn > 0.02 or top_zn > 0.02:
                interactions.append(
                    "Zinc present with chrome-tin pink — zinc destroys pink color development"
                )

        # High iron stacking (too dark)
        combined_fe = base_fe + top_fe
        if combined_fe > 0.15:
            interactions.append(
                f"Very high combined iron ({combined_fe:.3f}) — result may be too dark/black"
            )
        if combined_fe > 0.4:
            interactions.append(
                f"CRITICAL: Combined iron ({combined_fe:.3f}) exceeds practical layering threshold — expect muddy/uninteresting result"
            )

        # Cobalt + manganese interaction
        if (base_co > 0.005 or top_co > 0.005) and (base_mn > 0.005 or top_mn > 0.005):
            interactions.append(
                "Cobalt + manganese combination — can produce interesting purple/brown but unpredictable"
            )

        # Chrome contamination risk
        if base_cr > 0.001 or top_cr > 0.001:
            interactions.append(
                "Chromium present — can migrate and discolor surrounding glazes in the kiln"
            )

        return interactions
