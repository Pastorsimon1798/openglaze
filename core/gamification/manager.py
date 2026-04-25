"""Gamification manager: CRUD for stats, badges, activity."""

import json
import logging
from typing import Optional

from .models import UserStats, Badge, ActivityLog
from .badges import check_badges
from .streaks import update_streak

logger = logging.getLogger(__name__)


class GamificationManager:
    """Manages user gamification state."""

    def __init__(self, conn):
        self.conn = conn

    def get_stats(self, user_id: str) -> Optional[UserStats]:
        """Get user stats, initializing if needed."""
        cursor = self.conn.execute(
            "SELECT * FROM user_stats WHERE user_id = ?", (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            self.conn.execute("INSERT INTO user_stats (user_id) VALUES (?)", (user_id,))
            self.conn.commit()
            cursor = self.conn.execute(
                "SELECT * FROM user_stats WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
        return UserStats.from_dict(dict(row)) if row else None

    def get_badges(self, user_id: str) -> list:
        """Get all badges for a user."""
        cursor = self.conn.execute(
            "SELECT * FROM badges WHERE user_id = ? ORDER BY earned_at DESC", (user_id,)
        )
        return [Badge.from_dict(dict(b)) for b in cursor.fetchall()]

    def get_activity(self, user_id: str, limit: int = 10) -> list:
        """Get recent activity for a user."""
        cursor = self.conn.execute(
            """SELECT * FROM activity_log WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit),
        )
        return [ActivityLog.from_dict(dict(a)) for a in cursor.fetchall()]

    def log_activity(self, user_id: str, activity_type: str, metadata: dict = None):
        """Log an activity and update streak."""
        self.conn.execute(
            """INSERT INTO activity_log (user_id, activity_type, metadata) VALUES (?, ?, ?)""",
            (user_id, activity_type, json.dumps(metadata) if metadata else None),
        )
        update_streak(self.conn, user_id)

    def on_combination_tested(
        self, user_id: str, combo_id: int, status: str, is_surprise: bool = False
    ):
        """Called when a combination result is submitted."""
        # Update stats
        self.conn.execute(
            """INSERT INTO user_stats (user_id) VALUES (?)
               ON CONFLICT(user_id) DO UPDATE SET
               combinations_tested = combinations_tested + 1,
               combinations_proven = CASE WHEN ? IN ('proven', 'surprise') THEN combinations_proven + 1 ELSE combinations_proven END,
               surprises_found = CASE WHEN ? = 1 THEN surprises_found + 1 ELSE surprises_found END,
               discoveries_count = discoveries_count + 1,
               updated_at = CURRENT_TIMESTAMP""",
            (user_id, status, 1 if is_surprise else 0),
        )

        # Log activity
        self.log_activity(
            user_id,
            "combination_tested",
            {"combination_id": combo_id, "status": status},
        )

        # Check for new badges
        stats = self.get_stats(user_id)
        if stats:
            check_badges(self.conn, user_id, stats.to_dict())

    def on_prediction_resolved(self, user_id: str, correct: bool, points: int = 10):
        """Called when a prediction is resolved."""
        if correct:
            self.conn.execute(
                """UPDATE user_stats SET points = points + ?,
                   predictions_correct = predictions_correct + 1,
                   predictions_total = predictions_total + 1
                   WHERE user_id = ?""",
                (points, user_id),
            )
        else:
            self.conn.execute(
                """UPDATE user_stats SET predictions_total = predictions_total + 1
                   WHERE user_id = ?""",
                (user_id,),
            )
