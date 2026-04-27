#!/usr/bin/env python3
"""Seed OpenGlaze demo database with community glazes and sample data."""

import json
import os
import sqlite3
import sys

import yaml
from core.db import connect_db
from datetime import datetime, timedelta

DEMO_USER_ID = "demo-user-001"

ALLOWED_TABLES = {
    "activity_log",
    "predictions",
    "badges",
    "user_stats",
    "combinations",
    "glazes",
}

PRESET_COMBINATIONS = [
    {
        "a": "Clear Gloss",
        "b": "Ocean Blue",
        "status": "proven",
        "rating": 4,
        "desc": "Transparent base over cobalt blue = reliable layering with vibrant color.",
    },
    {
        "a": "Clear Gloss",
        "b": "Honey Amber",
        "status": "proven",
        "rating": 5,
        "desc": "Transparent base lets iron-amber show through beautifully.",
    },
    {
        "a": "Celadon",
        "b": "Temmoku",
        "status": "proven",
        "rating": 5,
        "desc": "Classic combo: transparent iron-green over iron-brown = great breaks.",
    },
    {
        "a": "Matte White",
        "b": "Ocean Blue",
        "status": "proven",
        "rating": 4,
        "desc": "Matte opaque over glossy opaque = nice surface contrast.",
    },
    {
        "a": "Satin Clear",
        "b": "Copper Red",
        "status": "proven",
        "rating": 4,
        "desc": "Satin transparent over copper semi-opaque = subtle depth.",
    },
    {
        "a": "Shino",
        "b": "Iron Red",
        "status": "tested",
        "rating": 2,
        "desc": "Shino crawl risk + iron bleed through semi-opaque shino.",
    },
    {
        "a": "Ocean Blue",
        "b": "Forest Green",
        "status": "tested",
        "rating": 3,
        "desc": "Cobalt-blue over copper-green can produce murky blue-green tones.",
    },
    {
        "a": "Temmoku",
        "b": "Chocolate Brown",
        "status": "tested",
        "rating": 2,
        "desc": "Both iron-heavy, too dark, no contrast.",
    },
    {
        "a": "Satin Black",
        "b": "Copper Red",
        "status": "surprise",
        "rating": 4,
        "desc": "Copper+iron+manganese interaction creates unexpected metallic sheen.",
        "rarity": "uncommon",
    },
    {
        "a": "Rutile Blue",
        "b": "Clear Gloss",
        "status": "proven",
        "rating": 4,
        "desc": "Rutile over clear = classic reliable combo.",
    },
    {
        "a": "Chun Blue",
        "b": "Cream",
        "status": "proven",
        "rating": 4,
        "desc": "Pale cobalt blue over warm cream = delicate contrast.",
    },
    {
        "a": "Penny Vein",
        "b": "Glossy Black",
        "status": "tested",
        "rating": 3,
        "desc": "Textured veins partially hidden by opaque black.",
    },
]


def get_db():
    conn = connect_db("glaze.db")
    conn.row_factory = sqlite3.Row
    return conn


def seed_glazes(conn, glazes):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM glazes WHERE user_id = ?", (DEMO_USER_ID,))
    if cursor.fetchone()[0] > 0:
        return cursor.execute(
            "SELECT COUNT(*) FROM glazes WHERE user_id = ?", (DEMO_USER_ID,)
        ).fetchone()[0]
    allowed = ("transparent", "opaque", "matte", "satin", "gloss")
    for g in glazes:
        bt = g.get("base_type", "gloss")
        if bt not in allowed:
            bt = "gloss"
        cursor.execute(
            "INSERT INTO glazes (id, user_id, name, cone, atmosphere, base_type, surface, color, transparency, notes, recipe) VALUES (?,?,?, ?,?,?, ?,?,?, ?,?)",
            (
                g["name"],
                DEMO_USER_ID,
                g["name"],
                g.get("cone", "5"),
                g.get("atmosphere", "oxidation"),
                bt,
                g.get("surface"),
                g.get("color"),
                g.get("transparency"),
                g.get("notes", ""),
                json.dumps(g.get("recipe", [])),
            ),
        )
    conn.commit()
    count = cursor.execute(
        "SELECT COUNT(*) FROM glazes WHERE user_id = ?", (DEMO_USER_ID,)
    ).fetchone()[0]
    print(f"Seeded {count} glazes")
    return count


def seed_demo_stats(conn):
    cursor = conn.cursor()
    if (
        cursor.execute(
            "SELECT COUNT(*) FROM user_stats WHERE user_id = ?", (DEMO_USER_ID,)
        ).fetchone()[0]
        > 0
    ):
        return
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO user_stats (user_id,points,current_streak,longest_streak,streak_freeze_remaining,last_activity_date,combinations_tested,combinations_proven,surprises_found,predictions_correct,predictions_total,discoveries_count) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (DEMO_USER_ID, 150, 7, 7, 2, today, 12, 8, 1, 7, 10, 14),
    )
    conn.commit()
    print("Seeded demo stats")


def seed_badges(conn):
    cursor = conn.cursor()
    if (
        cursor.execute(
            "SELECT COUNT(*) FROM badges WHERE user_id = ?", (DEMO_USER_ID,)
        ).fetchone()[0]
        > 0
    ):
        return
    for bt, bn, bi in [
        ("streak_7", "Week Warrior", "7-day streak"),
        ("proven_10", "Trusted Tester", "10 proven"),
        ("surprise_hunter", "Surprise Hunter", "5 surprises"),
    ]:
        cursor.execute(
            "INSERT INTO badges (user_id,badge_type,badge_name,badge_icon) VALUES (?,?,?,?)",
            (DEMO_USER_ID, bt, bn, bi),
        )
    conn.commit()
    print("Seeded badges")


def seed_combinations(conn):
    cursor = conn.cursor()
    if (
        cursor.execute(
            "SELECT COUNT(*) FROM combinations WHERE user_id = ?", (DEMO_USER_ID,)
        ).fetchone()[0]
        > 0
    ):
        return
    seeded = 0
    for c in PRESET_COMBINATIONS:
        if not cursor.execute(
            "SELECT id FROM glazes WHERE user_id=? AND name=?", (DEMO_USER_ID, c["a"])
        ).fetchone():
            continue
        if not cursor.execute(
            "SELECT id FROM glazes WHERE user_id=? AND name=?", (DEMO_USER_ID, c["b"])
        ).fetchone():
            continue
        is_s = c["status"] == "surprise"
        cursor.execute(
            "INSERT INTO combinations (user_id,base,top,type,source,result,result_rating,is_surprise,surprise_rarity,discovered_by,status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                DEMO_USER_ID,
                c["a"],
                c["b"],
                "user-prediction",
                "fired",
                c["desc"],
                c["rating"],
                1 if is_s else 0,
                c.get("rarity"),
                DEMO_USER_ID,
                c["status"],
            ),
        )
        seeded += 1
    conn.commit()
    print(f"Seeded {seeded} combinations")


def seed_predictions(conn):
    cursor = conn.cursor()
    if (
        cursor.execute(
            "SELECT COUNT(*) FROM predictions WHERE user_id = ?", (DEMO_USER_ID,)
        ).fetchone()[0]
        > 0
    ):
        return
    combos = cursor.execute(
        "SELECT id, status, base, top FROM combinations WHERE user_id=?",
        (DEMO_USER_ID,),
    ).fetchall()
    outcomes = [
        "Beautiful result",
        "Compatible colors",
        "Interesting texture",
        "May need thinner application",
        "Unexpected interaction",
    ]
    for co in combos:
        outcome = outcomes[hash(co["base"] + co["top"]) % len(outcomes)]
        correct = co["status"] in ("proven", "surprise")
        cursor.execute(
            "INSERT INTO predictions (user_id,combination_id,predicted_outcome,confidence,is_ai,ai_prediction,ai_confidence,resolved,user_correct,points_earned) VALUES (?,?,?,?,0,?,?,1,?,?)",
            (
                DEMO_USER_ID,
                co["id"],
                outcome,
                50 + (hash(co["base"]) % 40),
                outcome if correct else "May need testing",
                65,
                1 if correct else 0,
                10 if correct else 0,
            ),
        )
    conn.commit()
    print(f"Seeded predictions for {len(combos)} combos")


def seed_activity_log(conn):
    cursor = conn.cursor()
    if (
        cursor.execute(
            "SELECT COUNT(*) FROM activity_log WHERE user_id = ?", (DEMO_USER_ID,)
        ).fetchone()[0]
        > 0
    ):
        return
    now = datetime.now()
    for i, (at, m) in enumerate(
        [
            ("combination_tested", '{"combination_id":1}'),
            ("prediction_made", '{"combination_id":2}'),
            ("combination_tested", '{"combination_id":3}'),
            ("streak_maintained", '{"streak_days":7}'),
        ]
    ):
        created = (now - timedelta(days=3 - i)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO activity_log (user_id,activity_type,metadata,created_at) VALUES (?,?,?,?)",
            (DEMO_USER_ID, at, m, created),
        )
    conn.commit()
    print("Seeded activity log")


def reset_demo(conn):
    for table in [
        "activity_log",
        "predictions",
        "badges",
        "user_stats",
        "combinations",
        "glazes",
    ]:
        if table not in ALLOWED_TABLES:
            raise ValueError(f"Invalid table name: {table}")
        conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (DEMO_USER_ID,))
    conn.commit()


if __name__ == "__main__":
    # Ensure database schema exists before seeding
    db_path = "glaze.db"
    try:
        from server import init_db

        init_db(db_path)
    except Exception as e:
        print(f"Warning: could not auto-initialize DB: {e}")
    conn = get_db()
    try:
        if "--reset" in sys.argv:
            reset_demo(conn)

        # Try ceramics-foundation submodule path first, fall back to templates/
        template_path = None
        try:
            from core.chemistry.data_loader import get_template_path as _get_tpl

            template_path = _get_tpl("default", "member-cone5-oxidation.yaml")
        except ImportError:
            pass
        if not template_path or not os.path.exists(template_path):
            template_path = os.path.join("templates", "default-cone5-bmix.yaml")
        print(f"Loading glazes from: {template_path}")
        with open(template_path, "r") as f:
            glazes = yaml.safe_load(f).get("glazes", [])

        # Also load community templates from ceramics-foundation/data/ if available
        for community_file in [
            "cone6-oxidation-community.yaml",
            "cone10-reduction-community.yaml",
        ]:
            community_path = None
            try:
                from core.chemistry.data_loader import (
                    get_community_template_path as _get_community,
                )

                community_path = _get_community(community_file)
            except ImportError:
                pass
            if not community_path or not os.path.exists(community_path):
                community_path = os.path.join("templates", community_file)
            if os.path.exists(community_path):
                print(f"Loading community template: {community_path}")
                with open(community_path, "r") as f:
                    community_glazes = yaml.safe_load(f).get("glazes", [])
                glazes.extend(community_glazes)
        count = seed_glazes(conn, glazes)
        seed_demo_stats(conn)
        seed_badges(conn)
        seed_combinations(conn)
        seed_predictions(conn)
        seed_activity_log(conn)
        print(f"\nDone! Seeded {count} community glazes.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        conn.close()
