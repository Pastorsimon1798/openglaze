"""Glaze management operations."""

from core.db import connect_db
import sqlite3
from typing import List, Optional

from .models import Glaze


class GlazeManager:
    """Manages glaze CRUD operations."""

    # Allowed column names for UPDATE statements
    ALLOWED_COLUMNS = {
        "name",
        "family",
        "color",
        "hex",
        "chemistry",
        "behavior",
        "layering",
        "warning",
        "recipe",
        "catalog_code",
        "notes",
    }

    def __init__(self, db_path: str = "glaze.db", user_id: Optional[str] = None):
        """
        Initialize GlazeManager.

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

    def get_all(self) -> List[Glaze]:
        """Get all glazes for the current user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM glazes WHERE user_id = ? OR user_id IS NULL ORDER BY family, name",
                (self.user_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM glazes WHERE user_id IS NULL ORDER BY family, name"
            )

        rows = cursor.fetchall()
        conn.close()

        return [Glaze.from_dict(dict(row)) for row in rows]

    def get_by_id(self, glaze_id: str) -> Optional[Glaze]:
        """Get a glaze by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM glazes WHERE id = ? AND (user_id = ? OR user_id IS NULL)",
                (glaze_id, self.user_id),
            )
        else:
            cursor.execute(
                "SELECT * FROM glazes WHERE id = ? AND user_id IS NULL", (glaze_id,)
            )

        row = cursor.fetchone()
        conn.close()

        return Glaze.from_dict(dict(row)) if row else None

    def get_by_name(self, name: str) -> Optional[Glaze]:
        """Get a glaze by name."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM glazes WHERE name = ? AND (user_id = ? OR user_id IS NULL)",
                (name, self.user_id),
            )
        else:
            cursor.execute(
                "SELECT * FROM glazes WHERE name = ? AND user_id IS NULL", (name,)
            )

        row = cursor.fetchone()
        conn.close()

        return Glaze.from_dict(dict(row)) if row else None

    def get_by_family(self, family: str) -> List[Glaze]:
        """Get glazes in a family (max 8)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT * FROM glazes WHERE family = ? AND (user_id = ? OR user_id IS NULL) ORDER BY name LIMIT 8",
                (family, self.user_id),
            )
        else:
            cursor.execute(
                "SELECT * FROM glazes WHERE family = ? AND user_id IS NULL ORDER BY name LIMIT 8",
                (family,),
            )

        rows = cursor.fetchall()
        conn.close()

        return [Glaze.from_dict(dict(row)) for row in rows]

    def create(self, glaze: Glaze) -> str:
        """Create a new glaze."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO glazes (id, name, family, color, hex, chemistry, behavior, layering, warning, recipe, catalog_code, notes, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                glaze.id,
                glaze.name,
                glaze.family,
                glaze.color,
                glaze.hex,
                glaze.chemistry,
                glaze.behavior,
                glaze.layering,
                glaze.warning,
                glaze.recipe,
                glaze.catalog_code,
                glaze.notes,
                self.user_id,  # Always use current user_id for new glazes
            ),
        )

        conn.commit()
        conn.close()

        return glaze.id

    def update(self, glaze_id: str, updates: dict) -> bool:
        """Update a glaze."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build dynamic update query
        set_clauses = []
        values = []
        for key, value in updates.items():
            if key != "id" and key != "user_id":  # Don't update id or user_id
                # Validate column name to prevent SQL injection
                if key not in self.ALLOWED_COLUMNS:
                    raise ValueError(f"Invalid column name: {key}")
                set_clauses.append(f"{key} = ?")
                values.append(value)

        if not set_clauses:
            conn.close()
            return False

        values.append(glaze_id)
        if self.user_id:
            values.append(self.user_id)
            query = f"UPDATE glazes SET {', '.join(set_clauses)} WHERE id = ? AND user_id = ?"
        else:
            query = f"UPDATE glazes SET {', '.join(set_clauses)} WHERE id = ? AND user_id IS NULL"

        cursor.execute(query, values)
        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def delete(self, glaze_id: str) -> bool:
        """Delete a glaze."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "DELETE FROM glazes WHERE id = ? AND user_id = ?",
                (glaze_id, self.user_id),
            )
        else:
            cursor.execute(
                "DELETE FROM glazes WHERE id = ? AND user_id IS NULL", (glaze_id,)
            )

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def search(self, query: str) -> List[Glaze]:
        """Search glazes by name, family, or notes (max 8 results)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        search_term = f"%{query}%"

        if self.user_id:
            cursor.execute(
                """
                SELECT * FROM glazes
                WHERE (user_id = ? OR user_id IS NULL)
                AND (name LIKE ? OR family LIKE ? OR notes LIKE ?)
                ORDER BY family, name
                LIMIT 8
            """,
                (self.user_id, search_term, search_term, search_term),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM glazes
                WHERE user_id IS NULL
                AND (name LIKE ? OR family LIKE ? OR notes LIKE ?)
                ORDER BY family, name
                LIMIT 8
            """,
                (search_term, search_term, search_term),
            )

        rows = cursor.fetchall()
        conn.close()

        return [Glaze.from_dict(dict(row)) for row in rows]

    def get_families(self) -> List[str]:
        """Get list of unique glaze families."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.user_id:
            cursor.execute(
                "SELECT DISTINCT family FROM glazes WHERE user_id = ? OR user_id IS NULL ORDER BY family",
                (self.user_id,),
            )
        else:
            cursor.execute(
                "SELECT DISTINCT family FROM glazes WHERE user_id IS NULL ORDER BY family"
            )

        rows = cursor.fetchall()
        conn.close()

        return [row["family"] for row in rows if row["family"]]
