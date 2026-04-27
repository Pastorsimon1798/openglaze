"""Studio data models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Studio:
    """Represents a collaborative studio group."""

    id: str = ""
    name: str = ""
    invite_code: str = ""
    created_by: str = ""
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Studio":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            invite_code=data.get("invite_code", ""),
            created_by=data.get("created_by", ""),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict:
        result = {"id": self.id, "name": self.name, "invite_code": self.invite_code}
        if self.created_by:
            result["created_by"] = self.created_by
        if self.created_at:
            result["created_at"] = self.created_at
        return result


@dataclass
class StudioMember:
    """Represents a member of a studio."""

    studio_id: str = ""
    user_id: str = ""
    display_name: str = ""
    role: str = "member"
    joined_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "StudioMember":
        return cls(
            studio_id=data.get("studio_id", ""),
            user_id=data.get("user_id", ""),
            display_name=data.get("display_name", ""),
            role=data.get("role", "member"),
            joined_at=data.get("joined_at"),
        )

    def to_dict(self) -> dict:
        result = {
            "studio_id": self.studio_id,
            "user_id": self.user_id,
            "display_name": self.display_name,
            "role": self.role,
        }
        if self.joined_at:
            result["joined_at"] = self.joined_at
        return result


@dataclass
class LabAssignment:
    """Represents a lab queue claim on a combination."""

    id: Optional[int] = None
    studio_id: str = ""
    combination_id: int = 0
    assigned_to: Optional[str] = None
    claimed_at: Optional[str] = None
    status: str = "claimed"
    claimed_by_name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "LabAssignment":
        return cls(
            id=data.get("id"),
            studio_id=data.get("studio_id", ""),
            combination_id=data.get("combination_id", 0),
            assigned_to=data.get("assigned_to"),
            claimed_at=data.get("claimed_at"),
            status=data.get("status", "claimed"),
            claimed_by_name=data.get("claimed_by_name"),
        )

    def to_dict(self) -> dict:
        result = {
            "studio_id": self.studio_id,
            "combination_id": self.combination_id,
            "status": self.status,
        }
        if self.id is not None:
            result["id"] = self.id
        if self.assigned_to:
            result["assigned_to"] = self.assigned_to
        if self.claimed_at:
            result["claimed_at"] = self.claimed_at
        if self.claimed_by_name:
            result["claimed_by_name"] = self.claimed_by_name
        return result
