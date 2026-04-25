"""Streak update logic."""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def update_streak(conn, user_id: str):
    """Update user activity streak. Call after any qualifying activity."""
    today = datetime.now().strftime("%Y-%m-%d")

    cursor = conn.execute(
        "SELECT current_streak, last_activity_date FROM user_stats WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    if not row:
        return

    last_date = row["last_activity_date"]
    current_streak = row["current_streak"]

    if last_date:
        last = datetime.strptime(last_date, "%Y-%m-%d").date()
        today_date = datetime.now().date()
        delta = (today_date - last).days

        if delta == 0:
            return  # Already active today
        elif delta == 1:
            current_streak += 1
        else:
            current_streak = 1  # Reset streak
    else:
        current_streak = 1

    conn.execute(
        """UPDATE user_stats SET current_streak = ?, last_activity_date = ?,
           longest_streak = MAX(longest_streak, ?), updated_at = CURRENT_TIMESTAMP
           WHERE user_id = ?""",
        (current_streak, today, current_streak, user_id),
    )
