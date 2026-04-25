"""Launch-readiness contract tests for Docker, CI, and docs."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_compose():
    return yaml.safe_load((ROOT / "docker-compose.yml").read_text())


def test_default_compose_uses_writable_sqlite_volume_on_app_port():
    compose = load_compose()
    app = compose["services"]["openglaze"]

    env = dict(item.split("=", 1) for item in app["environment"])
    assert env["FLASK_PORT"] == "8768"
    assert env["DATABASE_PATH"] == "/data/glaze.db"
    assert "DATABASE_URL" not in env

    assert "openglaze_data:/data" in app["volumes"]
    assert "openglaze_uploads:/app/frontend/uploads" in app["volumes"]
    assert "openglaze_data" in compose["volumes"]
    assert "openglaze_uploads" in compose["volumes"]


def test_prod_compose_does_not_reference_missing_nginx_config():
    compose = load_compose()
    nginx = compose["services"]["nginx"]
    mounted_files = [
        v.split(":", 1)[0].removeprefix("./") for v in nginx.get("volumes", [])
    ]
    for relative in mounted_files:
        if relative and not relative.startswith(("certs", "openglaze_")):
            assert (ROOT / relative).exists(), f"compose references missing {relative}"


def test_ci_starts_container_and_checks_health_endpoint():
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "docker run" in ci
    assert "/health" in ci
    assert "curl" in ci
    assert "import flask" not in ci


def test_api_docs_match_current_public_routes():
    api = (ROOT / "docs/API.md").read_text()
    stale_paths = [
        "POST /api/auth/login",
        "POST /api/auth/register",
        "POST /api/uploads",
        "GET /api/gamification/stats",
        "GET /api/gamification/leaderboard",
    ]
    for path in stale_paths:
        assert path not in api

    current_paths = [
        "POST /api/auth/simple-login",
        "GET /api/auth/me",
        "POST /api/upload",
        "GET /api/stats",
        "GET /api/progress",
        "GET /api/predictions/leaderboard",
    ]
    for path in current_paths:
        assert path in api
