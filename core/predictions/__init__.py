"""Predictions module: human vs AI prediction market."""

from .manager import PredictionManager
from .market import generate_ai_prediction

__all__ = ["PredictionManager", "generate_ai_prediction"]
