"""Tests for the recipe optimizer."""

import pytest
from core.chemistry.optimizer import RecipeOptimizer, optimize_recipe


class TestRecipeOptimizer:
    """Test the RecipeOptimizer class."""

    def setup_method(self):
        self.optimizer = RecipeOptimizer()
        self.base_recipe = "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12"

    def test_optimize_target_cte(self):
        """Optimizer should suggest recipes close to target CTE."""
        result = self.optimizer.optimize(
            self.base_recipe, "target_cte", target_value=6.5, max_suggestions=3
        )
        assert result.success
        assert len(result.suggestions) > 0
        # Best suggestion should be very close to 6.5
        best = result.suggestions[0]
        assert abs(best.predicted_cte - 6.5) < 0.5
        assert best.score > 50

    def test_optimize_more_matte(self):
        """Optimizer should suggest recipes with lower SiO2:Al2O3 for matte."""
        result = self.optimizer.optimize(
            self.base_recipe, "more_matte", max_suggestions=5
        )
        assert result.success
        assert len(result.suggestions) > 0
        # At least one suggestion should cross into matte territory
        surfaces = [s.predicted_surface for s in result.suggestions]
        assert "matte" in surfaces or "satin" in surfaces
        # Best suggestion should have the highest score
        best = result.suggestions[0]
        assert best.score > 0

    def test_optimize_more_matte_threshold_bonus(self):
        """Crossing the matte threshold should give a score bonus."""
        result = self.optimizer.optimize(
            self.base_recipe, "more_matte", max_suggestions=5
        )
        matte_suggestions = [
            s for s in result.suggestions if s.predicted_surface == "matte"
        ]
        if matte_suggestions:
            # Matte-crossing suggestions should score higher than non-matte
            best_matte = matte_suggestions[0]
            non_matte = [
                s for s in result.suggestions if s.predicted_surface != "matte"
            ]
            if non_matte:
                assert best_matte.score > non_matte[-1].score

    def test_optimize_more_glossy(self):
        """Optimizer should suggest recipes with higher SiO2:Al2O3 for gloss."""
        # Start with a slightly lower-ratio recipe
        recipe = "Custer Feldspar 40, Silica 20, Whiting 18, EPK 22"
        result = self.optimizer.optimize(recipe, "more_glossy", max_suggestions=3)
        assert result.success
        assert len(result.suggestions) > 0
        best = result.suggestions[0]
        assert best.score > 0

    def test_optimize_reduce_running(self):
        """Optimizer should suggest recipes with higher SiO2:Al2O3."""
        result = self.optimizer.optimize(
            self.base_recipe, "reduce_running", max_suggestions=3
        )
        assert result.success
        assert len(result.suggestions) > 0
        best = result.suggestions[0]
        assert best.score > 0

    def test_optimize_reduce_alkali(self):
        """Optimizer should suggest recipes with lower KNaO."""
        result = self.optimizer.optimize(
            self.base_recipe, "reduce_alkali", max_suggestions=3
        )
        assert result.success
        assert len(result.suggestions) > 0
        best = result.suggestions[0]
        assert best.score > 0

    def test_optimize_reduce_cte(self):
        """Optimizer should suggest recipes with lower CTE."""
        result = self.optimizer.optimize(
            self.base_recipe, "reduce_cte", max_suggestions=3
        )
        assert result.success
        assert len(result.suggestions) > 0
        best = result.suggestions[0]
        assert best.predicted_cte < result.original_cte

    def test_optimize_increase_cte(self):
        """Optimizer should suggest recipes with higher CTE."""
        result = self.optimizer.optimize(
            self.base_recipe, "increase_cte", max_suggestions=3
        )
        assert result.success
        assert len(result.suggestions) > 0
        best = result.suggestions[0]
        assert best.predicted_cte > result.original_cte

    def test_optimize_invalid_target(self):
        """Unknown target should return empty suggestions."""
        result = self.optimizer.optimize(
            self.base_recipe, "invalid_target", max_suggestions=3
        )
        assert result.success
        assert len(result.suggestions) == 0

    def test_optimize_bad_recipe(self):
        """Bad recipe should return success=False."""
        result = self.optimizer.optimize(
            "not a real recipe", "reduce_cte", max_suggestions=3
        )
        assert not result.success
        assert result.error is not None

    def test_optimize_to_dict(self):
        """Result should serialize to dict."""
        result = self.optimizer.optimize(
            self.base_recipe, "reduce_cte", max_suggestions=2
        )
        d = result.to_dict()
        assert d["success"] is True
        assert "suggestions" in d
        assert len(d["suggestions"]) > 0
        assert "predicted_cte" in d["suggestions"][0]

    def test_convenience_function(self):
        """optimize_recipe convenience function should work."""
        result = optimize_recipe(
            self.base_recipe, "target_cte", target_value=6.5, max_suggestions=2
        )
        assert result.success
        assert len(result.suggestions) > 0

    def test_substitution_when_both_present(self):
        """Substitutions should work even when both materials are in recipe."""
        # Both silica and epk are in base_recipe
        result = self.optimizer.optimize(
            self.base_recipe, "more_matte", max_suggestions=5
        )
        assert result.success
        descriptions = [s.change_description for s in result.suggestions]
        # Should include the silica->epk substitution
        assert any("Replace silica with kaolin" in d for d in descriptions)
