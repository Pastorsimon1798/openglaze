"""Experiment management operations."""

from core.db import connect_db
import sqlite3
from typing import List, Optional
from datetime import datetime

from .models import Experiment


class ExperimentManager:
    """Manages 6-stage experiment pipeline."""

    # Allowed column names for UPDATE statements
    ALLOWED_COLUMNS = {
        "combination_id",
        "base_glaze",
        "top_glaze",
        "stage",
        "status",
        "prediction",
        "result",
        "rating",
        "notes",
        "photo",
        "completed_at",
        "clay_body",
        "firing_type",
        "cone",
        "confirmation",
        "fired_at",
        "application_method",
        "thickness",
        "drying_time",
        "cooling_notes",
        "atmosphere_notes",
        "fired_by",
        "studio_id",
    }

    def __init__(self, db_path: str = "glaze.db", user_id: Optional[str] = None):
        """
        Initialize ExperimentManager.

        Args:
            db_path: Path to SQLite database file
            user_id: User ID for multi-tenant mode (None for personal mode)
        """
        self.db_path = db_path
        self.user_id = user_id

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = connect_db(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all(self) -> List[Experiment]:
        """Get all experiments for the current user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM experiments WHERE user_id = ? OR user_id IS NULL ORDER BY created_at DESC",
                (self.user_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM experiments WHERE user_id IS NULL ORDER BY created_at DESC"
            )

        rows = cursor.fetchall()
        conn.close()

        return [Experiment.from_dict(dict(row)) for row in rows]

    def get_active(self) -> List[Experiment]:
        """Get active (in-progress) experiments."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM experiments WHERE status = 'in_progress' AND (user_id = ? OR user_id IS NULL)",
                (self.user_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM experiments WHERE status = 'in_progress' AND user_id IS NULL"
            )

        rows = cursor.fetchall()
        conn.close()

        return [Experiment.from_dict(dict(row)) for row in rows]

    def get_by_stage(self, stage: str) -> List[Experiment]:
        """Get experiments at a specific stage."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM experiments WHERE stage = ? AND (user_id = ? OR user_id IS NULL)",
                (stage, self.user_id),
            )
        else:
            cursor.execute(
                "SELECT * FROM experiments WHERE stage = ? AND user_id IS NULL",
                (stage,),
            )

        rows = cursor.fetchall()
        conn.close()

        return [Experiment.from_dict(dict(row)) for row in rows]

    def get_by_id(self, exp_id: int) -> Optional[Experiment]:
        """Get an experiment by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM experiments WHERE id = ? AND (user_id = ? OR user_id IS NULL)",
                (exp_id, self.user_id),
            )
        else:
            cursor.execute(
                "SELECT * FROM experiments WHERE id = ? AND user_id IS NULL", (exp_id,)
            )

        row = cursor.fetchone()
        conn.close()

        return Experiment.from_dict(dict(row)) if row else None

    def create(self, experiment: Experiment) -> int:
        """Create a new experiment."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO experiments (combination_id, base_glaze, top_glaze, stage, status, prediction, result, rating, notes, photo, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                experiment.combination_id,
                experiment.base_glaze,
                experiment.top_glaze,
                experiment.stage,
                experiment.status,
                experiment.prediction,
                experiment.result,
                experiment.rating,
                experiment.notes,
                experiment.photo,
                self.user_id,
            ),
        )

        last_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return last_id

    def update(self, exp_id: int, updates: dict) -> bool:
        """Update an experiment."""
        conn = self._get_connection()
        cursor = conn.cursor()

        set_clauses = []
        values = []
        for key, value in updates.items():
            if key not in ("id", "user_id", "created_at"):
                # Validate column name to prevent SQL injection
                if key not in self.ALLOWED_COLUMNS:
                    raise ValueError(f"Invalid column name: {key}")
                set_clauses.append(f"{key} = ?")
                values.append(value)

        if not set_clauses:
            conn.close()
            return False

        values.append(exp_id)
        if self.user_id:
            values.append(self.user_id)
            query = f"UPDATE experiments SET {', '.join(set_clauses)} WHERE id = ? AND user_id = ?"
        else:
            query = f"UPDATE experiments SET {', '.join(set_clauses)} WHERE id = ? AND user_id IS NULL"

        cursor.execute(query, values)
        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def advance_stage(self, exp_id: int) -> bool:
        """Advance experiment to next stage."""
        experiment = self.get_by_id(exp_id)
        if not experiment:
            return False

        stages = [
            "ideation",
            "prediction",
            "application",
            "firing",
            "analysis",
            "documentation",
        ]
        current_idx = (
            stages.index(experiment.stage) if experiment.stage in stages else 0
        )

        if current_idx >= len(stages) - 1:
            # Already at documentation, mark as completed
            return self.update(
                exp_id,
                {"status": "completed", "completed_at": datetime.now().isoformat()},
            )

        next_stage = stages[current_idx + 1]
        return self.update(exp_id, {"stage": next_stage})

    def set_status(self, exp_id: int, status: str) -> bool:
        """Set experiment status."""
        updates = {"status": status}
        if status == "completed":
            updates["completed_at"] = datetime.now().isoformat()
        return self.update(exp_id, updates)

    def record_result(
        self, exp_id: int, result: str, rating: int = None, photo: str = None
    ) -> bool:
        """Record experiment result (at analysis stage)."""
        updates = {"result": result}
        if rating is not None:
            updates["rating"] = rating
        if photo:
            updates["photo"] = photo
        return self.update(exp_id, updates)

    def archive(self, exp_id: int, archive_type: str = "successful") -> bool:
        """Archive a completed experiment."""
        experiment = self.get_by_id(exp_id)
        if not experiment:
            return False

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO archive (name, base_glaze, top_glaze, result, rating, notes, photo, type, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                experiment.display_name,
                experiment.base_glaze,
                experiment.top_glaze,
                experiment.result,
                experiment.rating,
                experiment.notes,
                experiment.photo,
                archive_type,
                self.user_id,
            ),
        )

        # Delete from experiments
        cursor.execute("DELETE FROM experiments WHERE id = ?", (exp_id,))

        conn.commit()
        conn.close()

        return True

    def delete(self, exp_id: int) -> bool:
        """Delete an experiment."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "DELETE FROM experiments WHERE id = ? AND user_id = ?",
                (exp_id, self.user_id),
            )
        else:
            cursor.execute(
                "DELETE FROM experiments WHERE id = ? AND user_id IS NULL", (exp_id,)
            )

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def get_all_with_photos(self) -> list:
        """Get all experiments and archived combos that have a photo."""
        conn = self._get_connection()
        cursor = conn.cursor()

        results = []

        # From experiments table
        if self.user_id:
            cursor.execute(
                'SELECT id, base_glaze, top_glaze, photo, rating, created_at FROM experiments WHERE photo IS NOT NULL AND photo != "" AND (user_id = ? OR user_id IS NULL) ORDER BY created_at DESC',
                (self.user_id,),
            )
        else:
            cursor.execute(
                'SELECT id, base_glaze, top_glaze, photo, rating, created_at FROM experiments WHERE photo IS NOT NULL AND photo != "" AND user_id IS NULL ORDER BY created_at DESC'
            )

        for row in cursor.fetchall():
            results.append(dict(row))

        # From archive table
        if self.user_id:
            cursor.execute(
                'SELECT id, base_glaze, top_glaze, photo, rating, created_at FROM archive WHERE photo IS NOT NULL AND photo != "" AND (user_id = ? OR user_id IS NULL) ORDER BY created_at DESC',
                (self.user_id,),
            )
        else:
            cursor.execute(
                'SELECT id, base_glaze, top_glaze, photo, rating, created_at FROM archive WHERE photo IS NOT NULL AND photo != "" AND user_id IS NULL ORDER BY created_at DESC'
            )

        for row in cursor.fetchall():
            results.append(dict(row))

        conn.close()
        return results

    def get_pipeline_stats(self) -> dict:
        """Get statistics for the experiment pipeline."""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {
            "total": 0,
            "by_stage": {},
            "by_status": {},
        }

        # Total count
        if self.user_id:
            cursor.execute(
                "SELECT COUNT(*) as count FROM experiments WHERE user_id = ? OR user_id IS NULL",
                (self.user_id,),
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) as count FROM experiments WHERE user_id IS NULL"
            )

        stats["total"] = cursor.fetchone()["count"]

        # By stage
        stages = [
            "ideation",
            "prediction",
            "application",
            "firing",
            "analysis",
            "documentation",
        ]
        for stage in stages:
            if self.user_id:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM experiments WHERE stage = ? AND (user_id = ? OR user_id IS NULL)",
                    (stage, self.user_id),
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM experiments WHERE stage = ? AND user_id IS NULL",
                    (stage,),
                )
            stats["by_stage"][stage] = cursor.fetchone()["count"]

        # By status
        statuses = ["pending", "in_progress", "completed", "failed"]
        for status in statuses:
            if self.user_id:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM experiments WHERE status = ? AND (user_id = ? OR user_id IS NULL)",
                    (status, self.user_id),
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM experiments WHERE status = ? AND user_id IS NULL",
                    (status,),
                )
            stats["by_status"][status] = cursor.fetchone()["count"]

        conn.close()
        return stats

    def log_firing_result(self, exp_id: int, log_data: dict) -> bool:
        """
        Record firing result with required field validation.
        Required: clay_body, firing_type, cone, confirmation.
        Sets fired_by and fired_at automatically.
        """
        from .models import Experiment

        # Validate required fields
        missing = [f for f in Experiment.REQUIRED_FIELDS if not log_data.get(f)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        updates = {
            "clay_body": log_data["clay_body"],
            "firing_type": log_data["firing_type"],
            "cone": log_data["cone"],
            "confirmation": log_data["confirmation"],
            "fired_at": datetime.now().isoformat(),
        }

        # Optional fields
        for key in (
            "application_method",
            "thickness",
            "drying_time",
            "cooling_notes",
            "atmosphere_notes",
            "fired_by",
            "result",
            "rating",
            "notes",
            "photo",
        ):
            if log_data.get(key) is not None:
                updates[key] = log_data[key]

        return self.update(exp_id, updates)

    def share_with_studio(self, exp_id: int, studio_id: str) -> bool:
        """Set studio_id on experiment so studio members can see it."""
        return self.update(exp_id, {"studio_id": studio_id})

    def get_studio_experiments(self, studio_id: str) -> List[Experiment]:
        """Get all experiments shared with a studio."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM experiments WHERE studio_id = ? ORDER BY fired_at DESC",
            (studio_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [Experiment.from_dict(dict(r)) for r in rows]
