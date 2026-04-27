"""Gamification data models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class UserStats:
    """User gamification statistics."""

    user_id: str = ""
    points: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    streak_freeze_remaining: int = 2
    last_activity_date: Optional[str] = None
    combinations_tested: int = 0
    combinations_proven: int = 0
    surprises_found: int = 0
    predictions_correct: int = 0
    predictions_total: int = 0
    discoveries_count: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "UserStats":
        return cls(
            user_id=data.get("user_id", ""),
            points=data.get("points", 0),
            current_streak=data.get("current_streak", 0),
            longest_streak=data.get("longest_streak", 0),
            streak_freeze_remaining=data.get("streak_freeze_remaining", 2),
            last_activity_date=data.get("last_activity_date"),
            combinations_tested=data.get("combinations_tested", 0),
            combinations_proven=data.get("combinations_proven", 0),
            surprises_found=data.get("surprises_found", 0),
            predictions_correct=data.get("predictions_correct", 0),
            predictions_total=data.get("predictions_total", 0),
            discoveries_count=data.get("discoveries_count", 0),
        )

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "points": self.points,
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "streak_freeze_remaining": self.streak_freeze_remaining,
            "last_activity_date": self.last_activity_date,
            "combinations_tested": self.combinations_tested,
            "combinations_proven": self.combinations_proven,
            "surprises_found": self.surprises_found,
            "predictions_correct": self.predictions_correct,
            "predictions_total": self.predictions_total,
            "discoveries_count": self.discoveries_count,
        }


@dataclass
class Badge:
    """An earned achievement badge."""

    id: Optional[int] = None
    user_id: str = ""
    badge_type: str = ""
    badge_name: str = ""
    badge_icon: Optional[str] = None
    earned_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Badge":
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id", ""),
            badge_type=data.get("badge_type", ""),
            badge_name=data.get("badge_name", ""),
            badge_icon=data.get("badge_icon"),
            earned_at=data.get("earned_at"),
        )

    def to_dict(self) -> dict:
        result = {
            "user_id": self.user_id,
            "badge_type": self.badge_type,
            "badge_name": self.badge_name,
        }
        if self.id is not None:
            result["id"] = self.id
        if self.badge_icon:
            result["badge_icon"] = self.badge_icon
        if self.earned_at:
            result["earned_at"] = self.earned_at
        return result


@dataclass
class ActivityLog:
    """Activity log entry for engagement tracking."""

    id: Optional[int] = None
    user_id: str = ""
    activity_type: str = ""
    metadata: Optional[str] = None  # JSON
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ActivityLog":
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id", ""),
            activity_type=data.get("activity_type", ""),
            metadata=data.get("metadata"),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict:
        result = {
            "user_id": self.user_id,
            "activity_type": self.activity_type,
        }
        if self.id is not None:
            result["id"] = self.id
        if self.metadata:
            result["metadata"] = self.metadata
        if self.created_at:
            result["created_at"] = self.created_at
        return result
