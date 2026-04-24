"""Ceramic glaze chemistry engine.

Provides UMF (Unity Molecular Formula) calculation, recipe parsing,
and layering compatibility analysis.
"""

from .materials import Material, get_material, get_all_materials
from .parser import RecipeParser, ParseResult, parse_recipe_string
from .umf import UMFResult, UMFAnalyzer, calculate_umf
from .compatibility import CompatibilityResult, CompatibilityAnalyzer
from .batch import BatchAnalyzer
from .defects import DefectAnalysis, DefectPredictor, predict_defects
from .substitutions import SubstitutionResult, SubstitutionEngine, suggest_substitutions
from .compare import RecipeComparison, RecipeComparator, compare_recipes

__all__ = [
    'Material',
    'get_material',
    'get_all_materials',
    'RecipeParser',
    'ParseResult',
    'parse_recipe_string',
    'UMFResult',
    'UMFAnalyzer',
    'calculate_umf',
    'CompatibilityResult',
    'CompatibilityAnalyzer',
    'BatchAnalyzer',
    'DefectAnalysis',
    'DefectPredictor',
    'predict_defects',
    'SubstitutionResult',
    'SubstitutionEngine',
    'suggest_substitutions',
    'RecipeComparison',
    'RecipeComparator',
    'compare_recipes',
]
