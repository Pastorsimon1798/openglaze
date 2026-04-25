"""Experiment data models."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ExperimentStage(str, Enum):
    """6-stage experiment pipeline."""

    IDEATION = "ideation"  # Decide what to test
    PREDICTION = "prediction"  # Forecast the outcome
    APPLICATION = "application"  # Apply layers, log process
    FIRING = "firing"  # Fire and record atmosphere
    ANALYSIS = "analysis"  # Compare prediction to actual
    DOCUMENTATION = "documentation"  # Document successful combos


class ExperimentStatus(str, Enum):
    """Experiment status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Experiment:
    """Represents a glaze layering experiment."""

    id: Optional[int] = None
    combination_id: Optional[int] = None
    base_glaze: str = ""
    top_glaze: str = ""
    stage: str = "ideation"
    status: str = "pending"
    prediction: Optional[str] = None
    result: Optional[str] = None
    rating: Optional[int] = None
    notes: Optional[str] = None
    photo: Optional[str] = None
    user_id: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    # Firing log fields
    clay_body: Optional[str] = None
    firing_type: Optional[str] = None
    cone: Optional[str] = None
    application_method: Optional[str] = None
    thickness: Optional[str] = None
    drying_time: Optional[str] = None
    cooling_notes: Optional[str] = None
    atmosphere_notes: Optional[str] = None
    confirmation: Optional[str] = None
    fired_by: Optional[str] = None
    fired_at: Optional[str] = None
    studio_id: Optional[str] = None

    REQUIRED_FIELDS = ["clay_body", "firing_type", "cone", "confirmation"]

    @classmethod
    def from_dict(cls, data: dict) -> "Experiment":
        """Create Experiment from dictionary."""
        return cls(
            id=data.get("id"),
            combination_id=data.get("combination_id"),
            base_glaze=data.get("base_glaze", ""),
            top_glaze=data.get("top_glaze", ""),
            stage=data.get("stage", "ideation"),
            status=data.get("status", "pending"),
            prediction=data.get("prediction"),
            result=data.get("result"),
            rating=data.get("rating"),
            notes=data.get("notes"),
            photo=data.get("photo"),
            user_id=data.get("user_id"),
            created_at=data.get("created_at"),
            completed_at=data.get("completed_at"),
            clay_body=data.get("clay_body"),
            firing_type=data.get("firing_type"),
            cone=data.get("cone"),
            application_method=data.get("application_method"),
            thickness=data.get("thickness"),
            drying_time=data.get("drying_time"),
            cooling_notes=data.get("cooling_notes"),
            atmosphere_notes=data.get("atmosphere_notes"),
            confirmation=data.get("confirmation"),
            fired_by=data.get("fired_by"),
            fired_at=data.get("fired_at"),
            studio_id=data.get("studio_id"),
        )

    def to_dict(self) -> dict:
        """Convert Experiment to dictionary."""
        result = {
            "base_glaze": self.base_glaze,
            "top_glaze": self.top_glaze,
            "stage": self.stage,
            "status": self.status,
        }
        if self.id is not None:
            result["id"] = self.id
        if self.combination_id is not None:
            result["combination_id"] = self.combination_id
        if self.prediction:
            result["prediction"] = self.prediction
        if self.result:
            result["result"] = self.result
        if self.rating is not None:
            result["rating"] = self.rating
        if self.notes:
            result["notes"] = self.notes
        if self.photo:
            result["photo"] = self.photo
        if self.user_id:
            result["user_id"] = self.user_id
        if self.created_at:
            result["created_at"] = self.created_at
        if self.completed_at:
            result["completed_at"] = self.completed_at
        if self.clay_body:
            result["clay_body"] = self.clay_body
        if self.firing_type:
            result["firing_type"] = self.firing_type
        if self.cone:
            result["cone"] = self.cone
        if self.application_method:
            result["application_method"] = self.application_method
        if self.thickness:
            result["thickness"] = self.thickness
        if self.drying_time:
            result["drying_time"] = self.drying_time
        if self.cooling_notes:
            result["cooling_notes"] = self.cooling_notes
        if self.atmosphere_notes:
            result["atmosphere_notes"] = self.atmosphere_notes
        if self.confirmation:
            result["confirmation"] = self.confirmation
        if self.fired_by:
            result["fired_by"] = self.fired_by
        if self.fired_at:
            result["fired_at"] = self.fired_at
        if self.studio_id:
            result["studio_id"] = self.studio_id
        return result

    @property
    def display_name(self) -> str:
        """Human-readable experiment name."""
        return f"{self.top_glaze} OVER {self.base_glaze}"

    @property
    def stage_order(self) -> int:
        """Get numeric order of current stage."""
        stages = [
            "ideation",
            "prediction",
            "application",
            "firing",
            "analysis",
            "documentation",
        ]
        return stages.index(self.stage) if self.stage in stages else 0
