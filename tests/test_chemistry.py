"""Tests for the chemistry engine — UMF, CTE, compatibility, parser."""

import pytest

from core.chemistry.umf import calculate_umf, UMFAnalyzer
from core.chemistry.thermal_expansion import calculate_cte, cte_compatibility, clay_body_compatibility
from core.chemistry.compatibility import CompatibilityAnalyzer
from core.chemistry.parser import parse_recipe_string
from core.chemistry.batch import calculate_batch


class TestParser:
    """Recipe parser tests."""

    def test_parse_simple_recipe(self):
        result = parse_recipe_string('Custer Feldspar 45, Silica 30, Whiting 15, EPK 10')
        assert result.success is True
        assert 'custer feldspar' in result.materials
        assert result.materials['custer feldspar'] == 45.0

    def test_parse_multi_word_material(self):
        """EPK Kaolin should resolve to EPK material."""
        result = parse_recipe_string('Custer Feldspar 45, Silica 30, Whiting 18, EPK Kaolin 12')
        assert result.success is True
        assert 'epk' in result.materials
        assert 'epk kaolin' not in result.materials

    def test_parse_unknown_material_warns(self):
        result = parse_recipe_string('Custer Feldspar 50, Unobtainium 25, Silica 25')
        assert result.success is True  # Partial parse succeeds
        assert any('unobtainium' in e.lower() for e in result.errors)
        assert 'custer feldspar' in result.materials

    def test_parse_normalizes_percentages(self):
        result = parse_recipe_string('Custer Feldspar 45, Silica 30, Whiting 15, EPK 12')
        # Sum = 102, should normalize to 100
        assert result.normalized is True
        total = sum(result.materials.values())
        assert abs(total - 100.0) < 0.1


class TestUMF:
    """UMF calculation tests."""

    def test_umf_celadon(self):
        result = calculate_umf('Custer Feldspar 45, Silica 25, Whiting 18, EPK 12')
        assert result.success is True
        assert result.umf_formula is not None
        assert result.umf_formula['SiO2'] > 4.0
        assert result.umf_formula['Al2O3'] > 0.3
        assert result.umf_formula['CaO'] > 0.4
        # Celadon should be glossy (high SiO2/Al2O3)
        assert result.surface_prediction == 'glossy'

    def test_umf_matte_glaze(self):
        # High alumina, lower silica = matte
        # EPK has high Al2O3 (37%) — increase EPK, reduce silica
        result = calculate_umf('Custer Feldspar 30, Silica 5, Whiting 15, EPK 40, Dolomite 10')
        assert result.success is True
        assert result.surface_prediction == 'matte'

    def test_umf_returns_cte(self):
        result = calculate_umf('Custer Feldspar 45, Silica 25, Whiting 18, EPK 12')
        assert result.thermal_expansion is not None
        # Typical stoneware glaze CTE: 5.5 - 7.5
        assert 5.0 <= result.thermal_expansion <= 8.0

    def test_umf_missing_materials_tracked(self):
        result = calculate_umf('Custer Feldspar 50, Unobtainium 25, Silica 25')
        assert result.success is True
        assert 'unobtainium' in [m.lower() for m in result.missing_materials]
        assert any('not found in database' in w.lower() for w in result.warnings)

    def test_umf_bad_recipe_fails(self):
        result = calculate_umf('not a real recipe')
        assert result.success is False
        assert result.recipe_parsed is False

    def test_umf_no_flux_fails(self):
        result = calculate_umf('Silica 50, Alumina 50')
        assert result.success is False
        assert 'No flux oxides found' in result.error


class TestThermalExpansion:
    """Thermal expansion coefficient tests."""

    def test_cte_typical_glaze(self):
        """CTE of a typical cone 10 glaze should be 5-8 ×10^-6/°C."""
        result = calculate_umf('Custer Feldspar 45, Silica 25, Whiting 18, EPK 12')
        cte = result.thermal_expansion
        assert cte is not None
        assert 5.0 <= cte <= 8.0, f'CTE {cte} outside expected range for stoneware glaze'

    def test_cte_high_alkali_glaze(self):
        """High-alkali glaze should have higher CTE."""
        high_alkali = calculate_umf('Nepheline Syenite 60, Silica 20, EPK 20')
        low_alkali = calculate_umf('Custer Feldspar 45, Silica 25, Whiting 18, EPK 12')
        assert high_alkali.thermal_expansion > low_alkali.thermal_expansion

    def test_cte_high_silica_glaze(self):
        """High-silica glaze should have lower CTE."""
        high_silica = calculate_umf('Custer Feldspar 30, Silica 50, Whiting 10, EPK 10')
        normal = calculate_umf('Custer Feldspar 45, Silica 25, Whiting 18, EPK 12')
        assert high_silica.thermal_expansion < normal.thermal_expansion

    def test_cte_compatibility_low(self):
        """Nearly identical glazes should have low thermal risk."""
        risk, mismatch, desc = cte_compatibility(6.5, 6.7)
        assert risk == 'low'
        assert abs(mismatch) < 0.5

    def test_cte_compatibility_high(self):
        """Very different CTEs should have high thermal risk."""
        risk, mismatch, desc = cte_compatibility(6.0, 9.0)
        assert risk == 'high'
        assert abs(mismatch) > 2.5

    def test_clay_body_compatibility_good_fit(self):
        result = clay_body_compatibility(6.2, 'stoneware')
        assert result['fit'] == 'good'
        assert 'within typical' in result['assessment'].lower()

    def test_clay_body_compatibility_crazing_risk(self):
        result = clay_body_compatibility(8.5, 'stoneware')
        assert result['fit'] == 'loose'
        assert 'crazing' in result['assessment'].lower()


class TestCompatibility:
    """Compatibility analysis tests."""

    def test_identical_glazes_compatible(self):
        recipe = 'Custer Feldspar 45, Silica 25, Whiting 18, EPK 12'
        analyzer = CompatibilityAnalyzer()
        result = analyzer.analyze(recipe, recipe, 'Glaze A', 'Glaze A')
        assert result.success is True
        assert result.compatible is True
        assert result.score >= 0.9
        assert result.thermal_expansion_risk == 'low'
        assert result.cte_base is not None
        assert result.cte_top is not None
        assert result.thermal_expansion_delta == 0.0

    def test_similar_glazes_compatible(self):
        base = 'Custer Feldspar 45, Silica 25, Whiting 18, EPK 12'
        top = 'Custer Feldspar 50, Silica 20, Whiting 15, EPK 15'
        analyzer = CompatibilityAnalyzer()
        result = analyzer.analyze(base, top, 'Base', 'Top')
        assert result.success is True
        assert result.compatible is True
        assert result.score >= 0.6

    def test_dissimilar_glazes_flagged(self):
        base = 'Custer Feldspar 40, Silica 15, Whiting 20, EPK 10, Dolomite 15'
        top = 'Custer Feldspar 60, Silica 30, Whiting 5, EPK 5'
        analyzer = CompatibilityAnalyzer()
        result = analyzer.analyze(base, top, 'Matte', 'Gloss')
        assert result.success is True
        # Should flag fluidity mismatch
        assert any('stiff' in f.lower() or 'fluid' in f.lower() for f in result.risk_factors + result.warnings)

    def test_shino_over_non_shino_blocked(self):
        analyzer = CompatibilityAnalyzer()
        result = analyzer.analyze(
            'Feldspar 50, Silica 30, Whiting 15, Kaolin 5',
            'Feldspar 40, Silica 20, Nepheline Syenite 30, Kaolin 10',
            'Celadon', 'Shino'
        )
        assert result.compatible is False
        assert result.score == 0.0
        assert any('shino' in f.lower() for f in result.risk_factors)

    def test_iron_copper_interaction_detected(self):
        base = 'Custer Feldspar 45, Silica 25, Whiting 18, EPK 12, Red Iron Oxide 8'
        top = 'Custer Feldspar 45, Silica 25, Whiting 18, EPK 12, Copper Oxide 2'
        analyzer = CompatibilityAnalyzer()
        result = analyzer.analyze(base, top, 'Iron Base', 'Copper Top')
        assert any('iron' in i.lower() and 'copper' in i.lower() for i in result.oxide_interactions)

    def test_missing_recipe_graceful(self):
        analyzer = CompatibilityAnalyzer()
        result = analyzer.analyze(None, 'Custer Feldspar 45, Silica 25, Whiting 18, EPK 12', 'Unknown', 'Known')
        assert result.success is True
        assert any('not parseable' in w.lower() for w in result.warnings)


class TestBatchCalculator:
    """Recipe scaling tests."""

    def test_scale_recipe(self):
        recipe = {'Feldspar': 45, 'Silica': 30, 'Whiting': 15, 'Kaolin': 10}
        result = calculate_batch(recipe, 5000)
        assert result['success'] is True
        assert result['total_grams'] == 5000.0
        assert result['batch']['Feldspar'] == 2250.0
        assert result['batch']['Silica'] == 1500.0

    def test_scale_from_string(self):
        result = calculate_batch('Feldspar 45, Silica 30, Whiting 15, Kaolin 10', 2000)
        assert result['success'] is True
        assert result['total_grams'] == 2000.0

    def test_scale_normalizes_percentages(self):
        recipe = {'Feldspar': 50, 'Silica': 30, 'Whiting': 15, 'Kaolin': 10}
        # Sum = 105, should normalize
        result = calculate_batch(recipe, 1000)
        assert result['success'] is True
        assert abs(sum(result['batch'].values()) - 1000.0) < 0.1

    def test_scale_bad_recipe_fails(self):
        result = calculate_batch('not a recipe', 1000)
        assert result['success'] is False
