"""Glaze data models."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class GlazeFamily(str, Enum):
    """Glaze families organized by primary characteristic."""

    CLEAR = "clear"
    WHITE = "white"
    NEUTRAL = "neutral"
    GREEN = "green"
    SHINO = "shino"
    BLUE = "blue"
    RED = "red"
    PURPLE = "purple"
    BROWN = "brown"
    YELLOW = "yellow"
    LUSTER = "luster"
    CRYSTAL = "crystal"
    OTHER = "other"


@dataclass
class Glaze:
    """Represents a glaze in the system."""

    id: str
    name: str
    family: Optional[str] = None
    color: Optional[str] = None
    hex: Optional[str] = None
    chemistry: Optional[str] = None
    behavior: Optional[str] = None
    layering: Optional[str] = None
    warning: Optional[str] = None
    recipe: Optional[str] = None
    catalog_code: Optional[str] = None
    food_safe: Optional[bool] = None
    notes: Optional[str] = None
    # Default Studio / gamification columns
    cone: Optional[str] = None
    atmosphere: Optional[str] = None
    base_type: Optional[str] = None
    surface: Optional[str] = None
    transparency: Optional[str] = None
    image_url: Optional[str] = None
    user_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Glaze":
        """Create Glaze from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            family=data.get("family"),
            color=data.get("color"),
            hex=data.get("hex"),
            chemistry=data.get("chemistry"),
            behavior=data.get("behavior"),
            layering=data.get("layering"),
            warning=data.get("warning"),
            recipe=data.get("recipe"),
            catalog_code=data.get("catalog_code"),
            food_safe=data.get("food_safe"),
            notes=data.get("notes"),
            cone=data.get("cone"),
            atmosphere=data.get("atmosphere"),
            base_type=data.get("base_type"),
            surface=data.get("surface"),
            transparency=data.get("transparency"),
            image_url=data.get("image_url"),
            user_id=data.get("user_id"),
        )

    def to_dict(self) -> dict:
        """Convert Glaze to dictionary."""
        result = {
            "id": self.id,
            "name": self.name,
            "family": self.family,
            "color": self.color,
            "hex": self.hex,
            "chemistry": self.chemistry,
            "behavior": self.behavior,
            "layering": self.layering,
            "warning": self.warning,
            "recipe": self.recipe,
            "catalog_code": self.catalog_code,
            "notes": self.notes,
            "user_id": self.user_id,
        }
        if self.food_safe is not None:
            result["food_safe"] = self.food_safe
        return result
