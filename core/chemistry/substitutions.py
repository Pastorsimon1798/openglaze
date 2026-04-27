"""Material substitution suggestions for ceramic glaze recipes.

Helps users replace unavailable materials with alternatives based on:
1. Known one-to-one substitutions from ceramics-foundation data
2. Chemistry-based suggestions (same oxide family, similar composition)
3. Parser feedback when materials can't be resolved
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .materials import get_material, MATERIALS
from .data_loader import load_material_substitutions

logger = logging.getLogger(__name__)


@dataclass
class SubstitutionSuggestion:
    """A single substitution suggestion."""

    original: str
    substitute: str
    ratio: float
    confidence: str  # 'high', 'medium', 'low'
    notes: str
    chemistry_impact: str = ""


@dataclass
class SubstitutionResult:
    """Result of substitution analysis for a recipe."""

    success: bool
    unknown_materials: List[str] = field(default_factory=list)
    suggestions: List[SubstitutionSuggestion] = field(default_factory=list)
    reformulated_recipe: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "unknown_materials": self.unknown_materials,
            "suggestions": [
                {
                    "original": s.original,
                    "substitute": s.substitute,
                    "ratio": s.ratio,
                    "confidence": s.confidence,
                    "notes": s.notes,
                    "chemistry_impact": s.chemistry_impact,
                }
                for s in self.suggestions
            ],
            "reformulated_recipe": self.reformulated_recipe,
            "error": self.error,
        }


class SubstitutionEngine:
    """Suggest material substitutions for glaze recipes."""

    def __init__(self):
        self._substitutions = load_material_substitutions()
        self._one_to_one: Dict[str, List[Dict]] = {}
        self._complex: Dict[str, Dict] = {}
        self._load_data()

    def _load_data(self):
        """Load substitution data into lookup structures."""
        if self._substitutions:
            for entry in self._substitutions.get("one_to_one", []):
                from_mat = entry["from"].lower()
                if from_mat not in self._one_to_one:
                    self._one_to_one[from_mat] = []
                self._one_to_one[from_mat].append(entry)

            for entry in self._substitutions.get("complex", []):
                from_mat = entry["from"].lower()
                self._complex[from_mat] = entry

    def suggest(self, material_name: str) -> List[SubstitutionSuggestion]:
        """Get substitution suggestions for a single material.

        Args:
            material_name: Name of the material to replace

        Returns:
            List of substitution suggestions ordered by confidence
        """
        name_lower = material_name.lower().strip()
        suggestions = []

        # 1. Check known one-to-one substitutions
        if name_lower in self._one_to_one:
            for entry in self._one_to_one[name_lower]:
                suggestions.append(
                    SubstitutionSuggestion(
                        original=material_name,
                        substitute=entry["to"],
                        ratio=entry["ratio"],
                        confidence="high",
                        notes=entry.get("notes")
                        or f"Direct substitution: use {entry['ratio']}× amount",
                    )
                )

        # 2. Check complex substitutions
        if name_lower in self._complex:
            entry = self._complex[name_lower]
            suggestions.append(
                SubstitutionSuggestion(
                    original=material_name,
                    substitute=entry["to"],
                    ratio=entry.get("ratio", "see notes"),
                    confidence="medium",
                    notes=entry.get("notes", "Complex substitution — test required"),
                )
            )
            # Also add alternatives if present
            for alt in entry.get("alternatives", []):
                suggestions.append(
                    SubstitutionSuggestion(
                        original=material_name,
                        substitute=alt,
                        ratio=entry.get("ratio", "see notes"),
                        confidence="medium",
                        notes=f"Alternative to {entry['to']}. {entry.get('notes', '')}",
                    )
                )

        # 3. Chemistry-based fallback suggestions
        material = get_material(material_name)
        if material:
            suggestions.extend(
                self._chemistry_based_suggestions(material_name, material)
            )

        # Deduplicate by substitute name
        seen = set()
        unique = []
        for s in suggestions:
            key = s.substitute.lower()
            if key not in seen:
                seen.add(key)
                unique.append(s)

        return unique

    def _chemistry_based_suggestions(
        self, name: str, material
    ) -> List[SubstitutionSuggestion]:
        """Find chemistry-based substitutes from the material database."""
        suggestions = []
        name_lower = name.lower()

        # Find materials with similar oxide profiles
        for canonical, other in MATERIALS.items():
            if canonical == name_lower:
                continue

            # Simple similarity: same primary oxide
            my_oxides = set(material.oxides.keys())
            other_oxides = set(other.oxides.keys())

            # If they share the main oxide and have similar composition
            shared = my_oxides & other_oxides
            if not shared:
                continue

            # Calculate similarity score based on oxide overlap
            total_oxides = my_oxides | other_oxides
            similarity = len(shared) / len(total_oxides) if total_oxides else 0

            if similarity >= 0.5:
                # Check if primary oxide percentages are close
                primary_oxide = max(material.oxides.items(), key=lambda x: x[1])[0]
                if primary_oxide in other.oxides:
                    my_pct = material.oxides[primary_oxide]
                    other_pct = other.oxides[primary_oxide]
                    pct_diff = abs(my_pct - other_pct) / max(my_pct, 1)

                    if pct_diff < 0.3:  # Within 30%
                        confidence = "high" if pct_diff < 0.15 else "medium"
                        ratio = my_pct / other_pct if other_pct > 0 else 1.0

                        suggestions.append(
                            SubstitutionSuggestion(
                                original=name,
                                substitute=other.name,
                                ratio=round(ratio, 2),
                                confidence=confidence,
                                notes=f"Similar chemistry: both are {primary_oxide}-rich. Test for fit.",
                                chemistry_impact=f"Primary oxide {primary_oxide}: {my_pct:.0f}% vs {other_pct:.0f}%",
                            )
                        )

        return suggestions

    def analyze_recipe(self, recipe_string: str) -> SubstitutionResult:
        """Analyze a recipe and suggest substitutions for unknown materials.

        Args:
            recipe_string: Recipe like "Custer Feldspar 45, Mystery Material 25, Silica 30"

        Returns:
            SubstitutionResult with suggestions and optional reformulated recipe
        """
        from .parser import parse_recipe_string

        parse_result = parse_recipe_string(recipe_string)
        if not parse_result.success:
            return SubstitutionResult(
                success=False,
                error=f"Could not parse recipe: {'; '.join(parse_result.errors)}",
            )

        unknowns = []
        suggestions = []

        # Find unknown materials from parser errors
        for err in parse_result.errors:
            if err.startswith("Unknown material:"):
                # Extract material name from error message
                mat_name = (
                    err.split('"')[1]
                    if '"' in err
                    else err.replace("Unknown material:", "").strip()
                )
                unknowns.append(mat_name)
                mat_suggestions = self.suggest(mat_name)
                suggestions.extend(mat_suggestions)

        # Note: We only suggest substitutions for unknown materials.
        # For known materials, the user can explicitly request alternatives
        # via the /api/chemistry/substitutions endpoint with a material name.

        # Try to build a reformulated recipe
        reformulated = None
        if unknowns and suggestions:
            reformulated = self._build_reformulated_recipe(
                recipe_string, parse_result.materials, suggestions
            )

        return SubstitutionResult(
            success=True,
            unknown_materials=unknowns,
            suggestions=suggestions,
            reformulated_recipe=reformulated,
        )

    def _build_reformulated_recipe(
        self,
        original_recipe: str,
        materials: Dict[str, float],
        suggestions: List[SubstitutionSuggestion],
    ) -> Optional[str]:
        """Attempt to build a reformulated recipe using substitutions."""
        # Build a map of unknown material -> best high-confidence substitute
        best_subs = {}
        for s in suggestions:
            if s.confidence in ("high", "medium"):
                orig_lower = s.original.lower()
                if orig_lower not in best_subs:
                    best_subs[orig_lower] = s

        if not best_subs:
            return None

        parts = []
        for mat, pct in materials.items():
            mat_lower = mat.lower()
            if mat_lower in best_subs:
                sub = best_subs[mat_lower]
                if isinstance(sub.ratio, (int, float)):
                    new_pct = round(pct * sub.ratio, 2)
                    parts.append(f"{sub.substitute} {new_pct}")
                else:
                    parts.append(f"{sub.substitute} {pct}")
            else:
                parts.append(f"{mat.title()} {pct}")

        return ", ".join(parts) if parts else None


def suggest_substitutions(recipe: str) -> SubstitutionResult:
    """Convenience function to analyze a recipe for substitutions."""
    engine = SubstitutionEngine()
    return engine.analyze_recipe(recipe)
