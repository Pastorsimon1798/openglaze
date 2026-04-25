"""Prediction data models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Prediction:
    """A user or AI prediction for a glaze combination."""

    id: Optional[int] = None
    user_id: str = ""
    combination_id: int = 0
    predicted_outcome: str = ""
    confidence: int = 50
    is_ai: bool = False
    ai_prediction: Optional[str] = None
    ai_confidence: Optional[int] = None
    resolved: bool = False
    user_correct: Optional[bool] = None
    points_earned: int = 0
    resolved_at: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Prediction":
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id", ""),
            combination_id=data.get("combination_id", 0),
            predicted_outcome=data.get("predicted_outcome", ""),
            confidence=data.get("confidence", 50),
            is_ai=data.get("is_ai", False),
            ai_prediction=data.get("ai_prediction"),
            ai_confidence=data.get("ai_confidence"),
            resolved=data.get("resolved", False),
            user_correct=data.get("user_correct"),
            points_earned=data.get("points_earned", 0),
            resolved_at=data.get("resolved_at"),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict:
        result = {
            "user_id": self.user_id,
            "combination_id": self.combination_id,
            "predicted_outcome": self.predicted_outcome,
            "confidence": self.confidence,
            "is_ai": self.is_ai,
        }
        if self.id is not None:
            result["id"] = self.id
        if self.ai_prediction:
            result["ai_prediction"] = self.ai_prediction
        if self.ai_confidence is not None:
            result["ai_confidence"] = self.ai_confidence
        if self.resolved:
            result["resolved"] = self.resolved
        if self.user_correct is not None:
            result["user_correct"] = self.user_correct
        if self.points_earned:
            result["points_earned"] = self.points_earned
        if self.resolved_at:
            result["resolved_at"] = self.resolved_at
        if self.created_at:
            result["created_at"] = self.created_at
        return result
