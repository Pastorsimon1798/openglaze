"""Recipe parser for ceramic glaze recipes.

Handles parsing recipe strings like:
  "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12, Red Iron Oxide 1.5"
into structured material:amount dictionaries.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .materials import get_material

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Result of parsing a recipe string."""

    success: bool
    materials: Optional[Dict[str, float]] = None  # canonical_name -> amount
    errors: List[str] = field(default_factory=list)
    normalized: bool = False


class RecipeParser:
    """Parse ceramic glaze recipe strings into structured data."""

    # Patterns that indicate commercial/proprietary glaze codes
    COMMERCIAL_PATTERNS = [
        r"laguna\s+lg[-\s]?\d+",
        r"aardvark\s+\w+[-\s]?\d+",
        r"glazy\s*#\d+",
        r"coyote\s+\w+",
        r"clay\s+planet",
        r"^tc[-\s]?\d+$",
        r"^ctg[-\s]?\d+$",
        r"^lg[-\s]?\d+$",
        r"^mbg\d+$",
    ]

    def parse(self, recipe_string: str) -> ParseResult:
        """Parse a recipe string into materials and amounts.

        Args:
            recipe_string: Recipe like "Custer Feldspar 45, Silica 25, Whiting 18"

        Returns:
            ParseResult with materials dict if successful.
        """
        if not recipe_string or not recipe_string.strip():
            return ParseResult(
                success=False,
                errors=["Empty recipe string"],
            )

        recipe_string = recipe_string.strip()

        # Check for commercial/proprietary codes first
        if self._is_commercial_code(recipe_string):
            return ParseResult(
                success=False,
                errors=[f"Commercial/proprietary code detected: {recipe_string}"],
            )

        # Split by comma, semicolon, or newline
        parts = re.split(r"[,\n;]", recipe_string)

        materials = {}
        errors = []
        total = 0.0

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Skip description-only text (no number)
            if not re.search(r"\d", part):
                # Could be a recipe name like "Malcom Davis Shino - widely shared community recipe"
                # These aren't parseable as recipes
                continue

            # Extract material name and amount
            match = re.match(r"^(.+?)\s+([\d.]+)\s*%?\s*$", part)
            if not match:
                errors.append(f'Could not parse: "{part}"')
                continue

            material_name = match.group(1).strip()
            amount = float(match.group(2))

            if amount <= 0:
                errors.append(f"Invalid amount for {material_name}: {amount}")
                continue

            # Look up material in database
            material = self._lookup_material(material_name)
            if material is None:
                errors.append(f'Unknown material: "{material_name}"')
                continue

            canonical = self._canonical_name(material_name)
            if canonical in materials:
                logger.debug(
                    f"Duplicate material {canonical} in recipe, summing amounts"
                )
                materials[canonical] += amount
            else:
                materials[canonical] = amount
            total += amount

        if errors and not materials:
            return ParseResult(success=False, errors=errors)

        if not materials:
            return ParseResult(
                success=False,
                errors=["No parseable materials found in recipe"],
            )

        # Normalize percentages to sum to 100
        normalized = False
        if abs(total - 100.0) > 0.1:
            for key in materials:
                materials[key] = round(materials[key] / total * 100, 2)
            normalized = True

        return ParseResult(
            success=True,
            materials=materials,
            errors=errors,
            normalized=normalized,
        )

    def _is_commercial_code(self, recipe: str) -> bool:
        """Detect if a recipe string is a commercial product code."""
        recipe_lower = recipe.lower().strip()

        for pattern in self.COMMERCIAL_PATTERNS:
            if re.search(pattern, recipe_lower):
                return True

        # Short codes (less than 15 chars, mostly alphanumeric with dashes)
        # that don't contain typical recipe words
        recipe_words = recipe_lower.split()
        if len(recipe_words) <= 3 and len(recipe_lower) < 20:
            typical_words = {
                "feldspar",
                "silica",
                "whiting",
                "kaolin",
                "clay",
                "oxide",
                "carbonate",
                "borate",
                "frit",
                "dolomite",
                "talc",
                "zinc",
                "epk",
                "ball",
                "nepheline",
                "flint",
                "rutile",
                "cobalt",
                "copper",
                "iron",
                "manganese",
                "chrome",
                "tin",
                "zirconium",
                "titanium",
                "bentonite",
                "wollastonite",
                "lithium",
                "strontium",
                "bone",
                "ash",
                "borax",
                "soda",
            }
            if not any(word in typical_words for word in recipe_words):
                return True

        return False

    def _lookup_material(self, name: str):
        """Look up a material by name in the database.

        Tries the full name first, then progressively shorter prefixes
        to handle inputs like 'EPK Kaolin' where 'EPK' is the known
        material and 'Kaolin' is a descriptor.
        """
        # Try full name first
        material = get_material(name)
        if material is not None:
            return material

        # Try progressively shorter names (remove last word each time)
        words = name.strip().split()
        for i in range(len(words) - 1, 0, -1):
            shorter = " ".join(words[:i])
            material = get_material(shorter)
            if material is not None:
                return material

        return None

    def _canonical_name(self, name: str) -> str:
        """Get the canonical lowercase name for a material."""
        from .materials import MATERIALS, _ALIAS_TO_CANONICAL

        # Try full name first
        material = get_material(name)
        if material:
            normalized = name.strip().lower()
            if normalized in MATERIALS:
                return normalized
            if normalized in _ALIAS_TO_CANONICAL:
                return _ALIAS_TO_CANONICAL[normalized]

        # Try progressively shorter names (same logic as _lookup_material)
        words = name.strip().split()
        for i in range(len(words) - 1, 0, -1):
            shorter = " ".join(words[:i])
            material = get_material(shorter)
            if material:
                normalized = shorter.lower()
                if normalized in MATERIALS:
                    return normalized
                if normalized in _ALIAS_TO_CANONICAL:
                    return _ALIAS_TO_CANONICAL[normalized]

        return name.strip().lower()


# Module-level convenience function
_default_parser = RecipeParser()


def parse_recipe_string(recipe: str) -> ParseResult:
    """Parse a recipe string using the default parser."""
    return _default_parser.parse(recipe)
