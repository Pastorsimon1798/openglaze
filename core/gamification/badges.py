"""Badge definitions and awarding logic."""

import logging

logger = logging.getLogger(__name__)

BADGE_DEFINITIONS = [
    ("glaze_pioneer", "Glaze Pioneer", "First to test 10 combinations"),
    ("mad_scientist", "Mad Scientist", "50 combinations tested"),
    ("surprise_hunter", "Surprise Hunter", "5 surprise discoveries"),
    ("ai_whisperer", "AI Whisperer", "Beat Kama accuracy for a month"),
    ("studio_elder", "Studio Elder", "Most tested combinations"),
    ("streak_7", "Week Warrior", "7-day activity streak"),
    ("streak_30", "Monthly Master", "30-day activity streak"),
    ("proven_10", "Trusted Tester", "10 proven combinations"),
]


def check_badges(conn, user_id: str, stats: dict) -> list:
    """Check and award new badges based on stats. Returns list of newly earned badges."""
    conditions = {
        "glaze_pioneer": stats.get("combinations_tested", 0) >= 10,
        "mad_scientist": stats.get("combinations_tested", 0) >= 50,
        "surprise_hunter": stats.get("surprises_found", 0) >= 5,
        "studio_elder": stats.get("combinations_tested", 0) >= 100,
        "streak_7": stats.get("current_streak", 0) >= 7,
        "streak_30": stats.get("current_streak", 0) >= 30,
        "proven_10": stats.get("combinations_proven", 0) >= 10,
    }

    newly_earned = []
    for badge_type, badge_name, badge_icon in BADGE_DEFINITIONS:
        if badge_type not in conditions:
            continue
        if not conditions[badge_type]:
            continue

        cursor = conn.execute(
            "SELECT id FROM badges WHERE user_id = ? AND badge_type = ?",
            (user_id, badge_type),
        )
        if not cursor.fetchone():
            conn.execute(
                """INSERT INTO badges (user_id, badge_type, badge_name, badge_icon)
                   VALUES (?, ?, ?, ?)""",
                (user_id, badge_type, badge_name, badge_icon),
            )
            newly_earned.append(
                {
                    "badge_type": badge_type,
                    "badge_name": badge_name,
                    "badge_icon": badge_icon,
                }
            )
            logger.info(f"Awarded badge '{badge_name}' to user {user_id}")

    return newly_earned
