"""Prediction manager: create, resolve, leaderboard."""

import logging

from .market import generate_ai_prediction

logger = logging.getLogger(__name__)


class PredictionManager:
    """Manages predictions for glaze combinations."""

    def __init__(self, conn):
        self.conn = conn

    def create_prediction(
        self, user_id: str, combo_id: int, predicted_outcome: str, confidence: int = 50
    ) -> dict:
        """Create a user prediction with AI prediction."""
        # Get combo info for AI prediction
        cursor = self.conn.execute(
            """
            SELECT c.base as glaze_a_name, c.top as glaze_b_name
            FROM combinations c WHERE c.id = ?
        """,
            (combo_id,),
        )
        combo_info = cursor.fetchone()

        ai_prediction, ai_confidence = generate_ai_prediction(
            dict(combo_info) if combo_info else None
        )

        cursor = self.conn.execute(
            """INSERT INTO predictions (user_id, combination_id, predicted_outcome,
               confidence, ai_prediction, ai_confidence)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                combo_id,
                predicted_outcome,
                confidence,
                ai_prediction,
                ai_confidence,
            ),
        )
        pred_id = cursor.lastrowid
        self.conn.commit()

        return {
            "id": pred_id,
            "ai_prediction": ai_prediction,
            "ai_confidence": ai_confidence,
        }

    def resolve_predictions(self, combo_id: int, status: str) -> list:
        """Resolve all pending predictions for a combination."""
        cursor = self.conn.execute(
            "SELECT id, predicted_outcome FROM predictions WHERE combination_id = ? AND resolved = 0",
            (combo_id,),
        )
        resolved = []
        for pred in cursor.fetchall():
            correct = status in ("proven", "surprise", "tested")
            points = 10 if correct else 0
            self.conn.execute(
                """UPDATE predictions SET resolved = 1, user_correct = ?, points_earned = ?,
                   resolved_at = CURRENT_TIMESTAMP WHERE id = ?""",
                (1 if correct else 0, points, pred["id"]),
            )
            resolved.append(
                {"prediction_id": pred["id"], "correct": correct, "points": points}
            )

        self.conn.commit()
        return resolved

    def get_leaderboard(self, user_id: str) -> dict:
        """Get user vs AI prediction accuracy."""
        # User stats
        cursor = self.conn.execute(
            """SELECT predictions_correct, predictions_total, points
               FROM user_stats WHERE user_id = ?""",
            (user_id,),
        )
        user_stats = cursor.fetchone()

        # AI stats
        cursor = self.conn.execute(
            """SELECT COUNT(*) as correct FROM predictions
               WHERE is_ai = 1 AND user_correct = 1 AND user_id = ?""",
            (user_id,),
        )
        ai_correct = cursor.fetchone()

        cursor = self.conn.execute(
            """SELECT COUNT(*) as total FROM predictions
               WHERE is_ai = 1 AND user_id = ?""",
            (user_id,),
        )
        ai_total = cursor.fetchone()

        user_acc = 0
        ai_acc = 0
        if user_stats and user_stats["predictions_total"] > 0:
            user_acc = (
                user_stats["predictions_correct"]
                / user_stats["predictions_total"]
                * 100
            )
        if ai_total and ai_total["total"] > 0:
            ai_acc = ai_correct["correct"] / ai_total["total"] * 100

        return {
            "user": {
                "correct": user_stats["predictions_correct"] if user_stats else 0,
                "total": user_stats["predictions_total"] if user_stats else 0,
                "accuracy": round(user_acc, 1),
                "points": user_stats["points"] if user_stats else 0,
            },
            "ai": {
                "correct": ai_correct["correct"] if ai_correct else 0,
                "total": ai_total["total"] if ai_total else 0,
                "accuracy": round(ai_acc, 1),
            },
        }
