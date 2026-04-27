"""Studio management: groups, members, and lab queue."""

import secrets
from core.db import connect_db
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from .models import Studio, StudioMember, LabAssignment

logger = logging.getLogger(__name__)

# Invite code alphabet — no ambiguous chars (0/O, 1/I/L)
_CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

# Stale claim threshold
CLAIM_TIMEOUT_DAYS = 14


class StudioManager:
    """Manages studio groups, membership, and lab queue assignments."""

    def __init__(self, db_path: str = "glaze.db", user_id: Optional[str] = None):
        self.db_path = db_path
        self.user_id = user_id

    def _get_connection(self) -> sqlite3.Connection:
        conn = connect_db(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _generate_invite_code(self, length: int = 6) -> str:
        """Generate a unique invite code."""
        return "".join(secrets.choice(_CODE_CHARS) for _ in range(length))

    # ---- Studio CRUD ----

    def create_studio(self, name: str, display_name: str) -> dict:
        """Create a studio and add the creator as admin. Returns studio dict."""
        conn = self._get_connection()
        cursor = conn.cursor()

        studio_id = f"studio_{secrets.token_urlsafe(12)}"
        invite_code = self._generate_invite_code()

        # Ensure unique invite code
        while True:
            cursor.execute(
                "SELECT 1 FROM studios WHERE invite_code = ?", (invite_code,)
            )
            if not cursor.fetchone():
                break
            invite_code = self._generate_invite_code()

        user_id = self.user_id or f"local_{secrets.token_urlsafe(8)}"
        now = datetime.now().isoformat()

        cursor.execute(
            "INSERT INTO studios (id, name, invite_code, created_by) VALUES (?, ?, ?, ?)",
            (studio_id, name, invite_code, user_id),
        )
        cursor.execute(
            "INSERT INTO studio_members (studio_id, user_id, display_name, role) VALUES (?, ?, ?, ?)",
            (studio_id, user_id, display_name, "admin"),
        )

        conn.commit()
        conn.close()

        return {
            "id": studio_id,
            "name": name,
            "invite_code": invite_code,
            "created_by": user_id,
            "created_at": now,
        }

    def join_by_code(
        self, invite_code: str, display_name: str, user_id: str
    ) -> Optional[dict]:
        """Join a studio by invite code. Returns studio dict or None."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM studios WHERE invite_code = ?", (invite_code.upper(),)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        studio = Studio.from_dict(dict(row))

        # Check if already a member
        cursor.execute(
            "SELECT 1 FROM studio_members WHERE studio_id = ? AND user_id = ?",
            (studio.id, user_id),
        )
        if cursor.fetchone():
            conn.close()
            return studio.to_dict()

        cursor.execute(
            "INSERT INTO studio_members (studio_id, user_id, display_name, role) VALUES (?, ?, ?, ?)",
            (studio.id, user_id, display_name, "member"),
        )
        conn.commit()
        conn.close()

        return studio.to_dict()

    def get_studio(self, studio_id: str) -> Optional[Studio]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM studios WHERE id = ?", (studio_id,))
        row = cursor.fetchone()
        conn.close()
        return Studio.from_dict(dict(row)) if row else None

    def get_members(self, studio_id: str) -> List[StudioMember]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM studio_members WHERE studio_id = ? ORDER BY joined_at",
            (studio_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [StudioMember.from_dict(dict(r)) for r in rows]

    def get_user_studios(self, user_id: str) -> List[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT s.*, sm.role, sm.display_name
               FROM studios s
               JOIN studio_members sm ON s.id = sm.studio_id
               WHERE sm.user_id = ?
               ORDER BY sm.joined_at""",
            (user_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                **Studio.from_dict(dict(r)).to_dict(),
                "role": r["role"],
                "display_name": r["display_name"],
            }
            for r in rows
        ]

    def remove_member(self, studio_id: str, user_id: str, admin_user_id: str) -> bool:
        """Remove a member. Admin only. Cannot remove self."""
        if admin_user_id == user_id:
            return False
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify caller is admin
        cursor.execute(
            "SELECT role FROM studio_members WHERE studio_id = ? AND user_id = ?",
            (studio_id, admin_user_id),
        )
        row = cursor.fetchone()
        if not row or row["role"] != "admin":
            conn.close()
            return False

        cursor.execute(
            "DELETE FROM studio_members WHERE studio_id = ? AND user_id = ?",
            (studio_id, user_id),
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def regenerate_invite_code(
        self, studio_id: str, admin_user_id: str
    ) -> Optional[str]:
        """Generate a new invite code. Admin only."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT role FROM studio_members WHERE studio_id = ? AND user_id = ?",
            (studio_id, admin_user_id),
        )
        row = cursor.fetchone()
        if not row or row["role"] != "admin":
            conn.close()
            return None

        new_code = self._generate_invite_code()
        cursor.execute(
            "UPDATE studios SET invite_code = ? WHERE id = ?", (new_code, studio_id)
        )
        conn.commit()
        conn.close()
        return new_code

    def delete_studio(self, studio_id: str, admin_user_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT role FROM studio_members WHERE studio_id = ? AND user_id = ?",
            (studio_id, admin_user_id),
        )
        row = cursor.fetchone()
        if not row or row["role"] != "admin":
            conn.close()
            return False

        cursor.execute("DELETE FROM lab_assignments WHERE studio_id = ?", (studio_id,))
        cursor.execute("DELETE FROM studio_members WHERE studio_id = ?", (studio_id,))
        cursor.execute("DELETE FROM studios WHERE id = ?", (studio_id,))
        conn.commit()
        conn.close()
        return True

    # ---- Lab Queue ----

    def get_lab_queue(self, studio_id: str) -> List[dict]:
        """Get all testable combos with their claim status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT c.*, la.id as assignment_id, la.assigned_to, la.claimed_at,
                      la.status as claim_status, la.claimed_by_name
               FROM combinations c
               LEFT JOIN lab_assignments la
                   ON la.combination_id = c.id AND la.studio_id = ?
               WHERE c.prediction_grade IN ('likely', 'possible', 'unlikely', 'unknown')
                 AND (la.status IS NULL OR la.status NOT IN ('completed', 'released'))
               ORDER BY c.prediction_grade, c.created_at""",
            (studio_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        results = []
        for r in rows:
            combo = dict(r)
            assignment_id = combo.pop("assignment_id", None)
            assigned_to = combo.pop("assigned_to", None)
            claimed_at = combo.pop("claimed_at", None)
            claim_status = combo.pop("claim_status", None)
            claimed_by_name = combo.pop("claimed_by_name", None)

            combo["claim"] = None
            if assignment_id and claim_status:
                combo["claim"] = {
                    "id": assignment_id,
                    "assigned_to": assigned_to,
                    "claimed_at": claimed_at,
                    "status": claim_status,
                    "claimed_by_name": claimed_by_name,
                }
            results.append(combo)
        return results

    def claim_combo(
        self, studio_id: str, combination_id: int, user_id: str, display_name: str
    ) -> Optional[LabAssignment]:
        """Claim a combo for testing. Returns the assignment or None."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check for existing active claim
        cursor.execute(
            """SELECT id, status FROM lab_assignments
               WHERE studio_id = ? AND combination_id = ?
               AND status NOT IN ('completed', 'released')""",
            (studio_id, combination_id),
        )
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return None  # Already claimed

        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO lab_assignments (studio_id, combination_id, assigned_to, claimed_at, status, claimed_by_name) VALUES (?, ?, ?, ?, ?, ?)",
            (studio_id, combination_id, user_id, now, "claimed", display_name),
        )
        assignment_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return LabAssignment(
            id=assignment_id,
            studio_id=studio_id,
            combination_id=combination_id,
            assigned_to=user_id,
            claimed_at=now,
            status="claimed",
            claimed_by_name=display_name,
        )

    def release_combo(self, studio_id: str, combination_id: int) -> bool:
        """Release a claimed combo back to the pool."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE lab_assignments SET status = 'released'
               WHERE studio_id = ? AND combination_id = ?
               AND status IN ('claimed', 'in_progress')""",
            (studio_id, combination_id),
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def get_my_claims(self, studio_id: str, user_id: str) -> List[LabAssignment]:
        """Get combos claimed by a specific user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT la.*, c.base, c.top, c.prediction_grade
               FROM lab_assignments la
               JOIN combinations c ON la.combination_id = c.id
               WHERE la.studio_id = ? AND la.assigned_to = ?
               AND la.status IN ('claimed', 'in_progress')
               ORDER BY la.claimed_at DESC""",
            (studio_id, user_id),
        )
        rows = cursor.fetchall()
        conn.close()
        return [LabAssignment.from_dict(dict(r)) for r in rows]

    def complete_claim(
        self, studio_id: str, combination_id: int, experiment_id: int
    ) -> bool:
        """Mark a lab claim as completed, linking to experiment result."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE lab_assignments SET status = 'completed'
               WHERE studio_id = ? AND combination_id = ?
               AND status IN ('claimed', 'in_progress')""",
            (studio_id, combination_id),
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def release_stale_claims(self) -> int:
        """Release claims older than CLAIM_TIMEOUT_DAYS. Call on startup."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=CLAIM_TIMEOUT_DAYS)).isoformat()

        cursor.execute(
            """UPDATE lab_assignments SET status = 'released'
               WHERE claimed_at < ?
               AND status IN ('claimed', 'in_progress')""",
            (cutoff,),
        )
        released = cursor.rowcount
        conn.commit()
        conn.close()

        if released:
            logger.info(f"Released {released} stale lab claims")
        return released
