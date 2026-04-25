"""Combination data models."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class CombinationType(str, Enum):
    """Types of glaze combinations."""

    RESEARCH_BACKED = (
        "research-backed"  # Backed by community/literature/chemistry, NOT fired by user
    )
    USER_PREDICTION = "user-prediction"  # User-created combo, no research backing
    CONFIRMED = "confirmed"  # User fired it, result matched prediction
    SURPRISE = "surprise"  # User fired it, result was different from prediction


class PredictionGrade(str, Enum):
    """Evidence strength for a combination prediction."""

    LIKELY = "likely"  # Multiple community sources + chemistry supports it
    POSSIBLE = "possible"  # Some community reports or chemistry is favorable
    UNLIKELY = "unlikely"  # Chemistry or community evidence says it will fail
    UNKNOWN = "unknown"  # No data available, pure guess
    CONFIRMED = "confirmed"  # User fired it, matched prediction
    SURPRISE = "surprise"  # User fired it, didn't match prediction


class RiskLevel(str, Enum):
    """Risk levels for combinations."""

    LOW = "low"  # Same chemistry, very likely to work
    MEDIUM = "medium"  # Some unknowns, may have issues
    HIGH = "high"  # Known risks (e.g., Shino over non-Shino)


class EffectType(str, Enum):
    """Visual effect types."""

    SUBTLE = "subtle"  # Minor color/surface changes
    DRAMATIC = "dramatic"  # Significant visual transformation


@dataclass
class Combination:
    """Represents a glaze layering combination."""

    id: Optional[int] = None
    base: str = ""  # Base glaze (applied first)
    top: str = ""  # Top glaze (applied last)
    layers: Optional[str] = None  # JSON array of layers, bottom to top
    type: str = "user-prediction"
    source: Optional[str] = None  # Where combo came from: 'fired', 'community', etc.
    result: Optional[str] = None  # Visual result description
    chemistry: Optional[str] = None  # Chemical explanation
    risk: Optional[str] = None
    effect: Optional[str] = None
    stage: str = "idea"  # Pipeline stage
    prediction_grade: str = "unknown"  # Evidence-based prediction grade
    notes: Optional[str] = None
    user_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Combination":
        """Create Combination from dictionary."""
        return cls(
            id=data.get("id"),
            base=data.get("base", ""),
            top=data.get("top", ""),
            layers=data.get("layers"),
            type=data.get("type", "user-prediction"),
            source=data.get("source"),
            result=data.get("result"),
            chemistry=data.get("chemistry"),
            risk=data.get("risk"),
            effect=data.get("effect"),
            stage=data.get("stage", "idea"),
            prediction_grade=data.get("prediction_grade", "unknown"),
            notes=data.get("notes"),
            user_id=data.get("user_id"),
        )

    def to_dict(self) -> dict:
        """Convert Combination to dictionary."""
        result = {
            "base": self.base,
            "top": self.top,
            "type": self.type,
            "stage": self.stage,
            "prediction_grade": self.prediction_grade,
        }
        if self.id is not None:
            result["id"] = self.id
        if self.layers:
            result["layers"] = self.layers
        if self.source:
            result["source"] = self.source
        if self.result:
            result["result"] = self.result
        if self.chemistry:
            result["chemistry"] = self.chemistry
        if self.risk:
            result["risk"] = self.risk
        if self.effect:
            result["effect"] = self.effect
        if self.notes:
            result["notes"] = self.notes
        if self.user_id:
            result["user_id"] = self.user_id
        return result

    @property
    def display_name(self) -> str:
        """Human-readable combination name."""
        return f"{self.top} OVER {self.base}"
