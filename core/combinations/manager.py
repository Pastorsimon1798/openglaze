"""Combination management operations."""

from typing import List, Optional, Dict
from collections import defaultdict
import sqlite3

from core.db import connect_db
from .models import Combination


class CombinationManager:
    """Manages glaze combination operations."""

    # Allowed column names for UPDATE statements
    ALLOWED_COLUMNS = {
        "base",
        "top",
        "layers",
        "type",
        "source",
        "result",
        "chemistry",
        "risk",
        "effect",
        "stage",
        "prediction_grade",
        "notes",
        "is_surprise",
        "surprise_rarity",
        "discovered_by",
        "status",
        "result_rating",
    }

    def __init__(self, db_path: str = "glaze.db", user_id: Optional[str] = None):
        """
        Initialize CombinationManager.

        Args:
            db_path: Path to SQLite database file
            user_id: User ID for multi-tenant mode (None for personal mode)
        """
        self.db_path = db_path
        self.user_id = user_id

    def _get_connection(self):
        """Get database connection."""
        conn = connect_db(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all(self) -> List[Combination]:
        """Get all combinations for the current user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM combinations WHERE user_id = ? OR user_id IS NULL ORDER BY base, top",
                (self.user_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM combinations WHERE user_id IS NULL ORDER BY base, top"
            )

        rows = cursor.fetchall()
        conn.close()

        return [Combination.from_dict(dict(row)) for row in rows]

    def get_research_backed(self) -> List[Combination]:
        """Get research-backed combinations only (replaces get_proven)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM combinations WHERE type = 'research-backed' AND (user_id = ? OR user_id IS NULL)",
                (self.user_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM combinations WHERE type = 'research-backed' AND user_id IS NULL"
            )

        rows = cursor.fetchall()
        conn.close()

        return [Combination.from_dict(dict(row)) for row in rows]

    def get_user_predictions(self) -> List[Combination]:
        """Get user-prediction combinations only (replaces get_hypotheses)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM combinations WHERE type = 'user-prediction' AND (user_id = ? OR user_id IS NULL)",
                (self.user_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM combinations WHERE type = 'user-prediction' AND user_id IS NULL"
            )

        rows = cursor.fetchall()
        conn.close()

        return [Combination.from_dict(dict(row)) for row in rows]

    def get_unsimulated(self) -> List[Combination]:
        """Get combinations that haven't been simulated yet."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM combinations WHERE prediction_grade = 'unknown' AND (user_id = ? OR user_id IS NULL)",
                (self.user_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM combinations WHERE prediction_grade = 'unknown' AND user_id IS NULL"
            )

        rows = cursor.fetchall()
        conn.close()

        return [Combination.from_dict(dict(row)) for row in rows]

    # Backward compatibility aliases
    def get_proven(self) -> List[Combination]:
        """Deprecated: use get_research_backed()."""
        return self.get_research_backed()

    def get_hypotheses(self) -> List[Combination]:
        """Deprecated: use get_user_predictions()."""
        return self.get_user_predictions()

    def get_grouped_by_base(self) -> Dict[str, List[Combination]]:
        """Get combinations grouped by base glaze."""
        combinations = self.get_all()
        grouped = defaultdict(list)
        for combo in combinations:
            grouped[combo.base].append(combo)
        return dict(grouped)

    def get_by_id(self, combo_id: int) -> Optional[Combination]:
        """Get a combination by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM combinations WHERE id = ? AND (user_id = ? OR user_id IS NULL)",
                (combo_id, self.user_id),
            )
        else:
            cursor.execute(
                "SELECT * FROM combinations WHERE id = ? AND user_id IS NULL",
                (combo_id,),
            )

        row = cursor.fetchone()
        conn.close()

        return Combination.from_dict(dict(row)) if row else None

    def create(self, combination: Combination) -> int:
        """Create a new combination."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO combinations (base, top, layers, type, source, result, chemistry, risk, effect, stage, prediction_grade, notes, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                combination.base,
                combination.top,
                combination.layers,
                combination.type,
                combination.source,
                combination.result,
                combination.chemistry,
                combination.risk,
                combination.effect,
                combination.stage,
                combination.prediction_grade,
                combination.notes,
                self.user_id,
            ),
        )

        last_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return last_id

    def update(self, combo_id: int, updates: dict) -> bool:
        """Update a combination."""
        conn = self._get_connection()
        cursor = conn.cursor()

        set_clauses = []
        values = []
        for key, value in updates.items():
            if key not in ("id", "user_id"):
                # Validate column name to prevent SQL injection
                if key not in self.ALLOWED_COLUMNS:
                    raise ValueError(f"Invalid column name: {key}")
                set_clauses.append(f"{key} = ?")
                values.append(value)

        if not set_clauses:
            conn.close()
            return False

        values.append(combo_id)
        if self.user_id:
            values.append(self.user_id)
            query = f"UPDATE combinations SET {', '.join(set_clauses)} WHERE id = ? AND user_id = ?"
        else:
            query = f"UPDATE combinations SET {', '.join(set_clauses)} WHERE id = ? AND user_id IS NULL"

        cursor.execute(query, values)
        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def delete(self, combo_id: int) -> bool:
        """Delete a combination."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "DELETE FROM combinations WHERE id = ? AND user_id = ?",
                (combo_id, self.user_id),
            )
        else:
            cursor.execute(
                "DELETE FROM combinations WHERE id = ? AND user_id IS NULL", (combo_id,)
            )

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def promote_to_confirmed(self, combo_id: int, result: str) -> bool:
        """Promote a combo to confirmed after firing and result matched prediction."""
        return self.update(
            combo_id,
            {
                "type": "confirmed",
                "prediction_grade": "confirmed",
                "stage": "documented",
                "result": result,
            },
        )

    def mark_as_surprise(self, combo_id: int, result: str) -> bool:
        """Mark a combo as surprise after firing and result differed from prediction."""
        return self.update(
            combo_id,
            {
                "type": "surprise",
                "prediction_grade": "surprise",
                "stage": "documented",
                "result": result,
            },
        )

    # Backward compatibility
    def promote_to_proven(self, combo_id: int, result: str) -> bool:
        """Deprecated: use promote_to_confirmed()."""
        return self.promote_to_confirmed(combo_id, result)

    def check_shino_warning(self, top: str, base: str) -> Optional[str]:
        """Check if a combination involves Shino layering issues."""
        top_lower = top.lower()
        base_lower = base.lower()

        if "shino" in top_lower and "shino" not in base_lower:
            return "WARNING: Shino over non-Shino glazes often CRAWLS"

        return None
