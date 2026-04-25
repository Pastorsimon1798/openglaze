"""Gamification module: points, streaks, badges, activity tracking."""

from .manager import GamificationManager
from .badges import check_badges, BADGE_DEFINITIONS
from .streaks import update_streak

__all__ = ["GamificationManager", "check_badges", "BADGE_DEFINITIONS", "update_streak"]
