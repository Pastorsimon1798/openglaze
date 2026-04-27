"""Recipe optimizer — compute recipe tweaks to hit target properties.

The goal is to eliminate guesswork and reduce the number of physical test
firings. Instead of a potter firing 3-4 test tiles to find the right silica
addition, the optimizer computes it.

Targets:
    - target_cte: float          → exact CTE match (e.g., 6.5)
    - reduce_cte / increase_cte  → direction-only
    - more_matte / more_glossy   → surface adjustment
    - reduce_alkali              → lower KNaO for durability
    - reduce_running             → higher SiO2:Al2O3 or lower B2O3

Strategy:
    Grid-search material percentage adjustments (±5/10/15%).
    Rank by: (1) achieves target, (2) minimal change from original,
    (3) recipe stays balanced (sums ~100%).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .parser import parse_recipe_string
from .umf import calculate_umf, UMFResult
from .materials import get_material


@dataclass
class RecipeSuggestion:
    """A single optimized recipe suggestion."""

    recipe: str
    change_description: str
    predicted_umf: Dict
    predicted_cte: float
    predicted_surface: str
    score: float  # 0-100, higher = closer to target
    distance_from_target: float


@dataclass
class OptimizationResult:
    """Result of recipe optimization."""

    success: bool
    original_recipe: str
    target: str
    original_cte: Optional[float]
    original_surface: Optional[str]
    suggestions: List[RecipeSuggestion]
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "original_recipe": self.original_recipe,
            "target": self.target,
            "original_cte": self.original_cte,
            "original_surface": self.original_surface,
            "suggestions": [
                {
                    "recipe": s.recipe,
                    "change_description": s.change_description,
                    "predicted_cte": s.predicted_cte,
                    "predicted_surface": s.predicted_surface,
                    "score": s.score,
                    "distance_from_target": s.distance_from_target,
                }
                for s in self.suggestions
            ],
            "error": self.error,
        }


class RecipeOptimizer:
    """Optimize glaze recipes to hit target properties with minimal changes."""

    # Common tweaks that potters use in practice
    STANDARD_ADJUSTMENTS = [-15, -10, -5, 5, 10, 15]
    LARGE_ADJUSTMENTS = [-30, -20, 20, 30]  # For surface changes needing big moves

    # Known substitution pairs: (from, to, description)
    SUBSTITUTIONS = [
        (
            "nepheline syenite",
            "custer feldspar",
            "Replace high-alkali nepheline with lower-alkali feldspar",
        ),
        (
            "custer feldspar",
            "nepheline syenite",
            "Replace feldspar with nepheline for more flux",
        ),
        (
            "whiting",
            "wollastonite",
            "Replace whiting with wollastonite (adds silica, less LOI)",
        ),
        ("epk", "ball clay", "Replace kaolin with ball clay (more flux, less alumina)"),
        (
            "silica",
            "epk",
            "Replace silica with kaolin (adds alumina, lowers CTE, more matte)",
        ),
        (
            "epk",
            "silica",
            "Replace kaolin with silica (raises SiO2:Al2O3, more glossy)",
        ),
    ]

    def optimize(
        self,
        recipe: str,
        target: str,
        target_value: Optional[float] = None,
        max_suggestions: int = 5,
    ) -> OptimizationResult:
        """Optimize a recipe toward a target property.

        Args:
            recipe: Original recipe string
            target: One of 'target_cte', 'reduce_cte', 'increase_cte',
                    'more_matte', 'more_glossy', 'reduce_alkali', 'reduce_running'
            target_value: Required for 'target_cte', optional hint for others
            max_suggestions: Number of suggestions to return

        Returns:
            OptimizationResult with ranked suggestions
        """
        # Parse and analyze original
        parse_result = parse_recipe_string(recipe)
        if not parse_result.success:
            return OptimizationResult(
                success=False,
                original_recipe=recipe,
                target=target,
                original_cte=None,
                original_surface=None,
                suggestions=[],
                error=f"Could not parse recipe: {parse_result.errors}",
            )

        original_materials = dict(parse_result.materials)
        original_umf = calculate_umf(recipe)
        if not original_umf.success:
            return OptimizationResult(
                success=False,
                original_recipe=recipe,
                target=target,
                original_cte=None,
                original_surface=None,
                suggestions=[],
                error=f"UMF calculation failed: {original_umf.error}",
            )

        original_cte = original_umf.thermal_expansion
        original_surface = original_umf.surface_prediction

        # Guard: surface targets require Al2O3 in the recipe
        sio2_al2o3 = original_umf.ratios.get("sio2_al2o3", 0.0)
        if (
            target in ("more_matte", "more_glossy", "reduce_running")
            and sio2_al2o3 == 0.0
        ):
            return OptimizationResult(
                success=True,
                original_recipe=recipe,
                target=target,
                original_cte=original_cte,
                original_surface=original_surface,
                suggestions=[],
                error="Recipe contains no alumina (Al2O3) — surface and running-risk optimization requires a glaze with structural alumina. Add kaolin, feldspar, or ball clay.",
            )

        # Guard: already at target CTE
        if (
            target == "target_cte"
            and target_value is not None
            and original_cte is not None
        ):
            if abs(original_cte - target_value) < 0.1:
                return OptimizationResult(
                    success=True,
                    original_recipe=recipe,
                    target=target,
                    original_cte=original_cte,
                    original_surface=original_surface,
                    suggestions=[],
                    error=f"Recipe CTE ({original_cte:.2f}) is already within 0.1 of target ({target_value:.2f}). No adjustment needed.",
                )

        # Build target evaluator
        evaluator = self._build_evaluator(
            target, target_value, original_cte, original_surface, original_umf
        )

        candidates: List[Tuple[str, str, UMFResult, float]] = []

        # Determine which adjustment set to use
        is_surface_target = target in ("more_matte", "more_glossy")
        adjustments = self.STANDARD_ADJUSTMENTS + (
            self.LARGE_ADJUSTMENTS if is_surface_target else []
        )

        # 1. Single-material adjustments
        for mat_name, amount in original_materials.items():
            material = get_material(mat_name)
            if not material:
                continue

            for delta in adjustments:
                new_amount = amount + delta
                if new_amount < 1:
                    continue

                new_materials = dict(original_materials)
                new_materials[mat_name] = new_amount

                # Normalize to 100%
                total = sum(new_materials.values())
                if total == 0:
                    continue
                new_materials = {
                    k: round(v / total * 100, 2) for k, v in new_materials.items()
                }

                candidate_recipe = self._materials_to_recipe(new_materials)
                candidate_umf = calculate_umf(candidate_recipe, cone=original_umf.cone)
                if candidate_umf.success:
                    score, distance = evaluator(candidate_umf)
                    desc = (
                        f"{material.name} {amount:.1f} → {new_materials[mat_name]:.1f}%"
                    )
                    candidates.append((candidate_recipe, desc, candidate_umf, score))

        # 2. Material substitutions
        for from_mat, to_mat, sub_desc in self.SUBSTITUTIONS:
            if from_mat not in original_materials:
                continue

            from_amount = original_materials[from_mat]
            to_material = get_material(to_mat)
            if not to_material:
                continue

            for ratio in [0.25, 0.5, 0.75, 1.0]:
                swap_amount = from_amount * ratio
                new_materials = dict(original_materials)
                new_materials[from_mat] = from_amount - swap_amount
                # If to_mat already present, add to it; otherwise create it
                new_materials[to_mat] = new_materials.get(to_mat, 0) + swap_amount

                # Remove near-zero materials
                new_materials = {k: v for k, v in new_materials.items() if v >= 0.5}

                total = sum(new_materials.values())
                if total == 0:
                    continue
                new_materials = {
                    k: round(v / total * 100, 2) for k, v in new_materials.items()
                }

                candidate_recipe = self._materials_to_recipe(new_materials)
                candidate_umf = calculate_umf(candidate_recipe, cone=original_umf.cone)
                if candidate_umf.success:
                    score, distance = evaluator(candidate_umf)
                    pct = int(ratio * 100)
                    desc = f"{sub_desc} ({pct}% swap)"
                    candidates.append((candidate_recipe, desc, candidate_umf, score))

        # 3. Add common materials if not present
        common_additions = {
            "silica": "Add silica",
            "epk": "Add kaolin",
            "whiting": "Add whiting",
            "custer feldspar": "Add feldspar",
        }
        for mat_key, add_desc in common_additions.items():
            if mat_key in original_materials:
                continue
            material = get_material(mat_key)
            if not material:
                continue

            for add_pct in [5, 10, 15]:
                new_materials = dict(original_materials)
                # Reduce all existing materials proportionally
                scale = (100 - add_pct) / 100
                new_materials = {k: v * scale for k, v in new_materials.items()}
                new_materials[mat_key] = float(add_pct)
                new_materials = {k: round(v, 2) for k, v in new_materials.items()}

                candidate_recipe = self._materials_to_recipe(new_materials)
                candidate_umf = calculate_umf(candidate_recipe, cone=original_umf.cone)
                if candidate_umf.success:
                    score, distance = evaluator(candidate_umf)
                    desc = f"{add_desc} {add_pct}%"
                    candidates.append((candidate_recipe, desc, candidate_umf, score))

        # Rank and deduplicate
        candidates.sort(key=lambda x: x[3], reverse=True)

        seen_recipes = set()
        suggestions = []
        for rec, desc, umf, score in candidates:
            # Skip candidates that don't improve toward target
            if score <= 0:
                continue

            # Deduplicate by rounding recipe to nearest 0.5%
            key = self._recipe_key(rec)
            if key in seen_recipes:
                continue
            seen_recipes.add(key)

            # Skip if change is too small (< 2% CTE change for CTE targets)
            if target.startswith("target_cte") and original_cte is not None:
                if abs(umf.thermal_expansion - original_cte) < 0.2:
                    continue

            if len(suggestions) >= max_suggestions:
                break

            suggestions.append(
                RecipeSuggestion(
                    recipe=rec,
                    change_description=desc,
                    predicted_umf=umf.umf_formula,
                    predicted_cte=umf.thermal_expansion,
                    predicted_surface=umf.surface_prediction,
                    score=round(score, 1),
                    distance_from_target=round(score, 3),  # reused field
                )
            )

        return OptimizationResult(
            success=True,
            original_recipe=recipe,
            target=target,
            original_cte=original_cte,
            original_surface=original_surface,
            suggestions=suggestions,
        )

    def _build_evaluator(
        self,
        target: str,
        target_value: Optional[float],
        original_cte: Optional[float],
        original_surface: str,
        original_umf: UMFResult,
    ):
        """Build a scoring function for a given target."""
        sio2_al2o3 = original_umf.ratios.get("sio2_al2o3", 5.0)
        knao = original_umf.umf_formula.get("K2O", 0) + original_umf.umf_formula.get(
            "Na2O", 0
        )
        b2o3 = original_umf.umf_formula.get("B2O3", 0)

        if target == "target_cte" and target_value is not None:

            def evaluator(umf: UMFResult) -> Tuple[float, float]:
                if umf.thermal_expansion is None:
                    return 0.0, 999.0
                distance = abs(umf.thermal_expansion - target_value)
                # Score: 100 at exact match, falls off with distance
                score = max(0, 100 - distance * 20)
                return score, distance

            return evaluator

        elif target == "reduce_cte":

            def evaluator(umf: UMFResult) -> Tuple[float, float]:
                if umf.thermal_expansion is None or original_cte is None:
                    return 0.0, 999.0
                reduction = original_cte - umf.thermal_expansion
                if reduction <= 0:
                    return 0.0, 999.0
                # Score by reduction amount, capped
                score = min(100, reduction * 25)
                return score, -reduction

            return evaluator

        elif target == "increase_cte":

            def evaluator(umf: UMFResult) -> Tuple[float, float]:
                if umf.thermal_expansion is None or original_cte is None:
                    return 0.0, 999.0
                increase = umf.thermal_expansion - original_cte
                if increase <= 0:
                    return 0.0, 999.0
                score = min(100, increase * 25)
                return score, -increase

            return evaluator

        elif target == "more_matte":
            # Cone-aware thresholds for matte boundary
            cone = original_umf.cone or 10
            if cone <= 3:
                matte_threshold = 3.0
            elif cone <= 6:
                matte_threshold = 3.5
            else:
                matte_threshold = 4.0

            def evaluator(umf: UMFResult) -> Tuple[float, float]:
                new_ratio = umf.ratios.get("sio2_al2o3", 5.0)
                if new_ratio >= sio2_al2o3:
                    return 0.0, 999.0
                reduction = sio2_al2o3 - new_ratio
                score = min(100, reduction * 20)
                # Huge bonus for crossing into matte territory
                if new_ratio < matte_threshold:
                    score += 50
                return score, -reduction

            return evaluator

        elif target == "more_glossy":
            cone = original_umf.cone or 10
            if cone <= 3:
                glossy_threshold = 4.0
            elif cone <= 6:
                glossy_threshold = 4.5
            else:
                glossy_threshold = 5.0

            def evaluator(umf: UMFResult) -> Tuple[float, float]:
                new_ratio = umf.ratios.get("sio2_al2o3", 5.0)
                if new_ratio <= sio2_al2o3:
                    return 0.0, 999.0
                increase = new_ratio - sio2_al2o3
                score = min(100, increase * 20)
                # Bonus for crossing into glossy territory
                if new_ratio > glossy_threshold:
                    score += 50
                return score, -increase

            return evaluator

        elif target == "reduce_alkali":

            def evaluator(umf: UMFResult) -> Tuple[float, float]:
                new_knao = umf.umf_formula.get("K2O", 0) + umf.umf_formula.get(
                    "Na2O", 0
                )
                if new_knao >= knao:
                    return 0.0, 999.0
                reduction = knao - new_knao
                score = min(100, reduction * 50)
                return score, -reduction

            return evaluator

        elif target == "reduce_running":

            def evaluator(umf: UMFResult) -> Tuple[float, float]:
                new_ratio = umf.ratios.get("sio2_al2o3", 5.0)
                new_b2o3 = umf.umf_formula.get("B2O3", 0)
                score = 0.0
                if new_ratio > sio2_al2o3:
                    score += (new_ratio - sio2_al2o3) * 15
                if new_b2o3 < b2o3:
                    score += (b2o3 - new_b2o3) * 30
                if score <= 0:
                    return 0.0, 999.0
                return min(100, score), -score

            return evaluator

        else:

            def evaluator(umf: UMFResult) -> Tuple[float, float]:
                return 0.0, 999.0

            return evaluator

    @staticmethod
    def _materials_to_recipe(materials: Dict[str, float]) -> str:
        """Convert a materials dict to a recipe string."""
        parts = []
        for name, amount in materials.items():
            material = get_material(name)
            display_name = material.name if material else name.title()
            parts.append(f"{display_name} {amount:.2f}")
        return ", ".join(parts)

    @staticmethod
    def _recipe_key(recipe: str) -> str:
        """Generate a deduplication key for a recipe."""
        parsed = parse_recipe_string(recipe)
        if not parsed.success:
            return recipe
        items = []
        for name, amount in sorted(parsed.materials.items()):
            items.append(f"{name}:{round(amount * 2) / 2:.1f}")
        return "|".join(items)


def optimize_recipe(
    recipe: str,
    target: str,
    target_value: Optional[float] = None,
    max_suggestions: int = 5,
) -> OptimizationResult:
    """Convenience function to optimize a recipe."""
    optimizer = RecipeOptimizer()
    return optimizer.optimize(recipe, target, target_value, max_suggestions)
