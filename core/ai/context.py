"""
ContextRetriever - RAG-style context injection for Kama.

Retrieves relevant glaze, chemistry, and combination data from the database
and formats it as markdown for injection into the system prompt.
"""

from core.db import connect_db
import sqlite3
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ContextRetriever:
    """
    Retrieves relevant context from the database for a user question.

    Builds an in-memory index of glaze names for fast O(n) matching,
    and queries chemistry_rules and combinations tables via SQL LIKE.
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._glaze_index: Dict[str, dict] = {}
        self._build_glaze_index()

    def _build_glaze_index(self) -> None:
        """Build a lowercase name -> row dict from the glazes table."""
        conn = connect_db(self._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, family, color, chemistry, behavior, warning FROM glazes"
        )
        for row in cursor.fetchall():
            key = row["name"].lower().strip()
            self._glaze_index[key] = {
                "name": row["name"],
                "family": row["family"],
                "color": row["color"],
                "chemistry": row["chemistry"],
                "behavior": row["behavior"],
                "warning": row["warning"],
            }
        conn.close()

    def _extract_glaze_names(self, question: str) -> List[str]:
        """Case-insensitive match of glaze names in the question."""
        q_lower = question.lower()
        found = []
        for name_lower in self._glaze_index:
            if name_lower in q_lower:
                found.append(name_lower)
        return found

    def _search_chemistry_rules(self, question: str) -> List[dict]:
        """SQL LIKE search across chemistry rules, limit 5."""
        # Extract meaningful words (skip common stop words)
        # NOTE: 'can', 'will', 'may' kept OUT of stop_words so ceramic queries
        # like "will this crawl" or "can I layer" still extract useful terms
        stop_words = {
            "what",
            "is",
            "the",
            "a",
            "an",
            "how",
            "why",
            "does",
            "do",
            "when",
            "where",
            "which",
            "would",
            "should",
            "could",
            "tell",
            "me",
            "about",
            "if",
            "my",
            "to",
            "and",
            "or",
            "of",
            "in",
            "for",
            "with",
            "on",
            "that",
            "this",
        }
        words = [
            w.strip("?,.!;:")
            for w in question.lower().split()
            if len(w.strip("?,.!;:")) > 2 and w.strip("?,.!;:") not in stop_words
        ]
        if not words:
            return []

        conn = connect_db(self._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Search for each word separately, collect unique rules
        seen = set()
        rows = []
        for word in words[:5]:  # limit to first 5 words to avoid explosion
            like = f"%{word}%"
            cursor.execute(
                """
                SELECT category, title, description
                FROM chemistry_rules
                WHERE title LIKE ? OR description LIKE ?
                   OR conditions LIKE ? OR outcomes LIKE ? OR caveats LIKE ?
                ORDER BY category, id
            """,
                (like, like, like, like, like),
            )
            for r in cursor.fetchall():
                key = r["title"]
                if key not in seen:
                    seen.add(key)
                    rows.append(
                        {
                            "category": r["category"],
                            "title": r["title"],
                            "description": r["description"],
                        }
                    )
                if len(rows) >= 5:
                    break
            if len(rows) >= 5:
                break

        conn.close()
        return rows[:5]

    def _search_combinations(self, glaze_names: List[str]) -> List[dict]:
        """Find combinations where base or top matches a mentioned glaze."""
        if not glaze_names:
            return []
        conn = connect_db(self._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        placeholders = ",".join(["?"] * len(glaze_names))
        cursor.execute(
            f"""
            SELECT base, top, type, result, risk, effect
            FROM combinations
            WHERE lower(base) IN ({placeholders})
               OR lower(top) IN ({placeholders})
            LIMIT 10
        """,
            glaze_names + glaze_names,
        )
        rows = [
            {
                "base": r["base"],
                "top": r["top"],
                "type": r["type"],
                "result": r["result"],
                "risk": r["risk"],
                "effect": r["effect"],
            }
            for r in cursor.fetchall()
        ]
        conn.close()
        return rows

    def _search_combinations_by_question(self, question: str) -> List[dict]:
        """Find combinations by keyword search on base/top/result columns."""
        # NOTE: 'can', 'will', 'may' kept OUT of stop_words for ceramic queries
        stop_words = {
            "what",
            "is",
            "the",
            "a",
            "an",
            "how",
            "why",
            "does",
            "do",
            "when",
            "where",
            "which",
            "would",
            "should",
            "could",
            "tell",
            "me",
            "about",
            "if",
            "my",
            "to",
            "and",
            "or",
            "of",
            "in",
            "for",
            "with",
            "on",
            "that",
            "this",
        }
        words = [
            w.strip("?,.!;:")
            for w in question.lower().split()
            if len(w.strip("?,.!;:")) > 2 and w.strip("?,.!;:") not in stop_words
        ]
        if not words:
            return []

        conn = connect_db(self._db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        seen = set()
        rows = []
        for word in words[:5]:
            like = f"%{word}%"
            cursor.execute(
                """
                SELECT base, top, type, result, risk, effect
                FROM combinations
                WHERE lower(base) LIKE ? OR lower(top) LIKE ?
                   OR result LIKE ?
                LIMIT 10
            """,
                (like, like, like),
            )
            for r in cursor.fetchall():
                key = (r["base"], r["top"])
                if key not in seen:
                    seen.add(key)
                    rows.append(
                        {
                            "base": r["base"],
                            "top": r["top"],
                            "type": r["type"],
                            "result": r["result"],
                            "risk": r["risk"],
                            "effect": r["effect"],
                        }
                    )
                if len(rows) >= 10:
                    break
            if len(rows) >= 10:
                break
        conn.close()
        return rows[:10]

    def _format_glazes(self, glaze_names: List[str]) -> str:
        """Format matched glazes as markdown."""
        lines = ["## Studio Glazes\n"]
        for name in glaze_names:
            g = self._glaze_index[name]
            lines.append(f"### {g['name']}")
            if g["family"]:
                lines.append(f"Family: {g['family']}")
            if g["color"]:
                lines.append(f"Color: {g['color']}")
            if g["chemistry"]:
                lines.append(f"Chemistry: {g['chemistry']}")
            if g["behavior"]:
                lines.append(f"Behavior: {g['behavior']}")
            if g["warning"]:
                lines.append(f"WARNING: {g['warning']}")
            lines.append("")
        return "\n".join(lines)

    def _format_rules(self, rules: List[dict]) -> str:
        """Format chemistry rules as markdown."""
        lines = ["## Chemistry Rules\n"]
        for r in rules:
            lines.append(f"- **{r['title']}** ({r['category']}): {r['description']}")
        lines.append("")
        return "\n".join(lines)

    def _format_combinations(self, combos: List[dict]) -> str:
        """Format combinations as markdown."""
        lines = ["## Known Combinations\n"]
        for c in combos:
            risk = f" (risk: {c['risk']})" if c.get("risk") else ""
            lines.append(f"- **{c['top']} OVER {c['base']}** [{c['type']}]{risk}")
            if c.get("result"):
                lines.append(f"  Result: {c['result']}")
        lines.append("")
        return "\n".join(lines)

    def retrieve(self, question: str) -> str:
        """
        Retrieve relevant context for a question, formatted as markdown.

        Returns empty string if nothing matched.
        """
        self._build_glaze_index()
        glaze_names = self._extract_glaze_names(question)
        rules = self._search_chemistry_rules(question)
        combos = self._search_combinations(glaze_names)
        if not combos:
            combos = self._search_combinations_by_question(question)

        sections = []
        if glaze_names:
            sections.append(self._format_glazes(glaze_names))
        if rules:
            sections.append(self._format_rules(rules))
        if combos:
            sections.append(self._format_combinations(combos))

        result = "\n".join(sections)

        # Safety limit
        if len(result) > 4000:
            result = result[:4000] + "\n... (context truncated)"

        return result
