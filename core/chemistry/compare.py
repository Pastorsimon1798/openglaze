"""Recipe comparison — show chemical differences between two glaze recipes.

Helps potters understand what changed when modifying a recipe,
or compare a tested glaze to a target formula.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .umf import calculate_umf


@dataclass
class RecipeDifference:
    """A single difference between two recipes."""

    category: str  # 'oxide', 'ratio', 'material', 'surface', 'cte'
    metric: str
    base_value: Optional[float]
    top_value: Optional[float]
    delta: Optional[float]
    delta_percent: Optional[float]
    interpretation: str


@dataclass
class RecipeComparison:
    """Full comparison between two glaze recipes."""

    success: bool
    base_name: str = ""
    top_name: str = ""
    differences: List[RecipeDifference] = field(default_factory=list)
    base_umf: Optional[Dict] = None
    top_umf: Optional[Dict] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "base_name": self.base_name,
            "top_name": self.top_name,
            "differences": [
                {
                    "category": d.category,
                    "metric": d.metric,
                    "base_value": d.base_value,
                    "top_value": d.top_value,
                    "delta": d.delta,
                    "delta_percent": d.delta_percent,
                    "interpretation": d.interpretation,
                }
                for d in self.differences
            ],
            "base_umf": self.base_umf,
            "top_umf": self.top_umf,
            "error": self.error,
        }


class RecipeComparator:
    """Compare two glaze recipes chemically."""

    def compare(
        self,
        recipe_a: str,
        recipe_b: str,
        name_a: str = "Recipe A",
        name_b: str = "Recipe B",
        cone: Optional[int] = None,
    ) -> RecipeComparison:
        """Compare two recipes and highlight chemical differences.

        Args:
            recipe_a: First recipe string
            recipe_b: Second recipe string
            name_a: Name for first recipe
            name_b: Name for second recipe
            cone: Target cone for analysis

        Returns:
            RecipeComparison with all differences and interpretations
        """
        umf_a = calculate_umf(recipe_a, cone=cone)
        umf_b = calculate_umf(recipe_b, cone=cone)

        if not umf_a.success:
            return RecipeComparison(success=False, error=f"{name_a}: {umf_a.error}")
        if not umf_b.success:
            return RecipeComparison(success=False, error=f"{name_b}: {umf_b.error}")

        differences = []

        # Compare all oxides in UMF
        all_oxides = set(umf_a.umf_formula.keys()) | set(umf_b.umf_formula.keys())
        for oxide in sorted(all_oxides):
            val_a = umf_a.umf_formula.get(oxide, 0)
            val_b = umf_b.umf_formula.get(oxide, 0)
            delta = round(val_b - val_a, 3)
            delta_pct = round((delta / val_a) * 100, 1) if val_a != 0 else None

            interpretation = self._interpret_oxide_change(oxide, val_a, val_b, delta)
            differences.append(
                RecipeDifference(
                    category="oxide",
                    metric=oxide,
                    base_value=val_a,
                    top_value=val_b,
                    delta=delta,
                    delta_percent=delta_pct,
                    interpretation=interpretation,
                )
            )

        # Compare ratios
        ratio_keys = set(umf_a.ratios.keys()) | set(umf_b.ratios.keys())
        for ratio in sorted(ratio_keys):
            val_a = umf_a.ratios.get(ratio, 0)
            val_b = umf_b.ratios.get(ratio, 0)
            delta = round(val_b - val_a, 2)

            interpretation = self._interpret_ratio_change(ratio, val_a, val_b, delta)
            differences.append(
                RecipeDifference(
                    category="ratio",
                    metric=ratio,
                    base_value=val_a,
                    top_value=val_b,
                    delta=delta,
                    delta_percent=None,
                    interpretation=interpretation,
                )
            )

        # Compare surface predictions
        if umf_a.surface_prediction != umf_b.surface_prediction:
            differences.append(
                RecipeDifference(
                    category="surface",
                    metric="surface_prediction",
                    base_value=None,
                    top_value=None,
                    delta=None,
                    delta_percent=None,
                    interpretation=f"{name_a} is {umf_a.surface_prediction}, {name_b} is {umf_b.surface_prediction}",
                )
            )

        # Compare CTE
        if umf_a.thermal_expansion is not None and umf_b.thermal_expansion is not None:
            cte_delta = round(umf_b.thermal_expansion - umf_a.thermal_expansion, 2)
            if abs(cte_delta) >= 0.1:
                if cte_delta > 0:
                    interp = f"{name_b} has higher CTE (+{cte_delta}). Higher crazing risk, lower shivering risk."
                else:
                    interp = f"{name_b} has lower CTE ({cte_delta}). Higher shivering risk, lower crazing risk."
                differences.append(
                    RecipeDifference(
                        category="cte",
                        metric="thermal_expansion",
                        base_value=umf_a.thermal_expansion,
                        top_value=umf_b.thermal_expansion,
                        delta=cte_delta,
                        delta_percent=(
                            round((cte_delta / umf_a.thermal_expansion) * 100, 1)
                            if umf_a.thermal_expansion
                            else None
                        ),
                        interpretation=interp,
                    )
                )

        return RecipeComparison(
            success=True,
            base_name=name_a,
            top_name=name_b,
            differences=differences,
            base_umf=umf_a.to_dict(),
            top_umf=umf_b.to_dict(),
        )

    def _interpret_oxide_change(
        self, oxide: str, val_a: float, val_b: float, delta: float
    ) -> str:
        """Generate human interpretation of an oxide change."""
        if abs(delta) < 0.01:
            return f"{oxide} is essentially unchanged"

        direction = "increased" if delta > 0 else "decreased"
        magnitude = abs(delta)

        interpretations = {
            "SiO2": {
                "increased": "More silica makes glaze more durable, harder, and glossier. May need higher temperature to melt.",
                "decreased": "Less silica makes glaze softer, more fluid, and potentially more matte.",
            },
            "Al2O3": {
                "increased": "More alumina makes glaze stiffer, more matte, and more durable. Raises melting point.",
                "decreased": "Less alumina makes glaze more fluid and glossier. May run more.",
            },
            "CaO": {
                "increased": "More calcium promotes satin/matte surfaces and increases hardness.",
                "decreased": "Less calcium reduces hardness and moves glaze toward glossier surfaces.",
            },
            "MgO": {
                "increased": "More magnesium promotes dry matte surfaces and can cause crawling.",
                "decreased": "Less magnesium reduces matte tendency and crawling risk.",
            },
            "K2O": {
                "increased": "More potassium increases flux and gloss but raises thermal expansion (crazing risk).",
                "decreased": "Less potassium reduces flux and gloss, lowers thermal expansion.",
            },
            "Na2O": {
                "increased": "More sodium increases flux and gloss but raises thermal expansion (crazing risk).",
                "decreased": "Less sodium reduces flux and gloss, lowers thermal expansion.",
            },
            "Fe2O3": {
                "increased": "More iron darkens color, promotes tenmoku/iron effects.",
                "decreased": "Less iron lightens color, reduces iron-based effects.",
            },
            "B2O3": {
                "increased": "More boron lowers melting point significantly. Running risk at high levels.",
                "decreased": "Less boron raises melting point. May need higher cone.",
            },
            "ZnO": {
                "increased": "More zinc promotes crystal formation and can cause crawling.",
                "decreased": "Less zinc reduces crystal tendency and crawling risk.",
            },
            "TiO2": {
                "increased": "More titanium increases opacity and can promote crystal growth.",
                "decreased": "Less titanium reduces opacity and crystal tendency.",
            },
        }

        interp = interpretations.get(oxide, {}).get(direction)
        if interp:
            return interp

        return f"{oxide} {direction} by {magnitude:.3f}"

    def _interpret_ratio_change(
        self, ratio: str, val_a: float, val_b: float, delta: float
    ) -> str:
        """Generate human interpretation of a ratio change."""
        if abs(delta) < 0.1:
            return f"{ratio} is essentially unchanged"

        direction = "increased" if delta > 0 else "decreased"

        interpretations = {
            "sio2_al2o3": {
                "increased": "Higher SiO₂:Al₂O₃ pushes glaze toward glossy. More durable, harder surface.",
                "decreased": "Lower SiO₂:Al₂O₃ pushes glaze toward matte. Softer, potentially more fluid.",
            },
            "flux_alumina": {
                "increased": "More flux relative to alumina = more fluid, glossier glaze.",
                "decreased": "Less flux relative to alumina = stiffer, more matte glaze.",
            },
        }

        interp = interpretations.get(ratio, {}).get(direction)
        if interp:
            return interp

        return f"{ratio} {direction} by {abs(delta):.2f}"


def compare_recipes(
    recipe_a: str,
    recipe_b: str,
    name_a: str = "Recipe A",
    name_b: str = "Recipe B",
    cone: Optional[int] = None,
) -> RecipeComparison:
    """Convenience function to compare two recipes."""
    comparator = RecipeComparator()
    return comparator.compare(recipe_a, recipe_b, name_a, name_b, cone)
