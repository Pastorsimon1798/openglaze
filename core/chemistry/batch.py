"""Batch processing for UMF analysis across all glazes and combinations."""

import logging
from typing import Dict, Optional, Union

from .umf import UMFAnalyzer, calculate_umf
from .compatibility import CompatibilityAnalyzer
from .parser import parse_recipe_string

logger = logging.getLogger(__name__)


def calculate_batch(
    recipe: Union[Dict[str, float], str], batch_size_grams: float, unit: str = "grams"
) -> Dict:
    """Scale a glaze recipe to a target batch size.

    Args:
        recipe: Dict of {material: percentage} or a recipe string.
        batch_size_grams: Target total batch weight in grams.
        unit: 'grams' or 'pounds'. If pounds, converts to grams first.

    Returns:
        Dict with scaled amounts, total, and original percentages.
    """
    # Parse if string
    if isinstance(recipe, str):
        parse_result = parse_recipe_string(recipe)
        if not parse_result.success:
            return {
                "success": False,
                "error": f'Could not parse recipe: {"; ".join(parse_result.errors)}',
            }
        materials = parse_result.materials
    else:
        materials = dict(recipe)

    if not materials:
        return {"success": False, "error": "No materials in recipe"}

    # Convert pounds to grams if needed
    target_grams = batch_size_grams
    if unit.lower() in ("lb", "lbs", "pound", "pounds"):
        target_grams = batch_size_grams * 453.592

    # Normalize percentages to sum to 100
    total_pct = sum(materials.values())
    if total_pct == 0:
        return {"success": False, "error": "Recipe percentages sum to zero"}

    normalized = {name: (pct / total_pct) * 100 for name, pct in materials.items()}

    # Scale to target batch size
    scaled = {
        name: round((pct / 100.0) * target_grams, 2) for name, pct in normalized.items()
    }

    return {
        "success": True,
        "batch": scaled,
        "total_grams": round(target_grams, 2),
        "unit": unit,
        "original_percentages": {
            name: round(pct, 2) for name, pct in normalized.items()
        },
    }


class BatchAnalyzer:
    """Batch UMF and compatibility analysis across all glazes and combinations."""

    def __init__(
        self, db_path: str, user_id: Optional[str] = None, cone: Optional[int] = None
    ):
        self.db_path = db_path
        self.user_id = user_id
        self.cone = cone
        self.umf_analyzer = UMFAnalyzer()
        self.compat_analyzer = CompatibilityAnalyzer()

    def analyze_all_glazes(self) -> Dict[str, dict]:
        """Calculate UMF for all glazes in the database.

        Returns:
            Dict mapping glaze name to UMF result dict.
        """
        from core.db import connect_db

        glazes = {}
        try:
            conn = connect_db(self.db_path)
            user_filter = ""
            params = []
            if self.user_id:
                user_filter = "WHERE user_id = ? OR user_id IS NULL"
                params.append(self.user_id)

            cursor = conn.cursor()
            cursor.execute(f"SELECT name, recipe FROM glazes {user_filter}", params)
            rows = cursor.fetchall()
            conn.close()

            for name, recipe in rows:
                if not recipe:
                    glazes[name] = {"success": False, "error": "No recipe available"}
                    continue

                umf = calculate_umf(recipe, cone=self.cone)
                glazes[name] = umf.to_dict()

        except Exception as e:
            logger.error(f"Batch glaze analysis failed: {e}")

        return glazes

    def analyze_all_combinations(self) -> Dict[int, dict]:
        """Calculate compatibility for all combinations in the database.

        Returns:
            Dict mapping combination ID to compatibility result dict.
        """
        from core.db import connect_db

        results = {}
        try:
            conn = connect_db(self.db_path)
            user_filter = ""
            params = []
            if self.user_id:
                user_filter = "WHERE user_id = ? OR user_id IS NULL"
                params.append(self.user_id)

            cursor = conn.cursor()
            cursor.execute(
                f"SELECT c.id, c.base, c.top, g1.recipe as base_recipe, g2.recipe as top_recipe "
                f"FROM combinations c "
                f"LEFT JOIN glazes g1 ON c.base = g1.name "
                f"LEFT JOIN glazes g2 ON c.top = g2.name "
                f"{user_filter}",
                params,
            )
            rows = cursor.fetchall()
            conn.close()

            for combo_id, base_name, top_name, base_recipe, top_recipe in rows:
                compat = self.compat_analyzer.analyze(
                    base_recipe=base_recipe,
                    top_recipe=top_recipe,
                    base_name=base_name or "",
                    top_name=top_name or "",
                    cone=self.cone,
                )
                results[combo_id] = compat.to_dict()

        except Exception as e:
            logger.error(f"Batch combination analysis failed: {e}")

        return results

    def generate_report(self) -> dict:
        """Generate a comprehensive analysis report.

        Returns:
            Dict with summary counts and per-glaze/per-combo details.
        """
        glaze_results = self.analyze_all_glazes()
        combo_results = self.analyze_all_combinations()

        # Summary counts
        glaze_total = len(glaze_results)
        glaze_parsed = sum(1 for r in glaze_results.values() if r.get("success"))
        glaze_failed = glaze_total - glaze_parsed

        combo_total = len(combo_results)
        combo_compatible = sum(
            1 for r in combo_results.values() if r.get("compatible") is True
        )
        combo_incompatible = sum(
            1 for r in combo_results.values() if r.get("compatible") is False
        )
        combo_unknown = combo_total - combo_compatible - combo_incompatible

        # Surface distribution
        surfaces = {}
        for r in glaze_results.values():
            surface = r.get("surface_prediction")
            if surface:
                surfaces[surface] = surfaces.get(surface, 0) + 1

        # Average compatibility score
        scores = [
            r.get("score", 0)
            for r in combo_results.values()
            if r.get("score") is not None
        ]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "summary": {
                "glazes": {
                    "total": glaze_total,
                    "parsed": glaze_parsed,
                    "failed": glaze_failed,
                },
                "combinations": {
                    "total": combo_total,
                    "compatible": combo_compatible,
                    "incompatible": combo_incompatible,
                    "unknown": combo_unknown,
                },
                "surface_distribution": surfaces,
                "average_compatibility_score": round(avg_score, 2),
            },
            "glazes": glaze_results,
            "combinations": combo_results,
        }
