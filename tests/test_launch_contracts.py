"""Launch-readiness contract tests for Docker, CI, and docs."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_compose():
    return yaml.safe_load((ROOT / "docker-compose.yml").read_text())


def test_default_compose_uses_postgres_with_env_substitution_on_app_port():
    compose = load_compose()
    app = compose["services"]["openglaze"]

    env = dict(item.split("=", 1) for item in app["environment"])
    assert "DATABASE_URL" in env
    assert "${POSTGRES_PASSWORD}" in env["DATABASE_URL"]
    assert "${BASE_URL:-http://localhost:8768}" == env["BASE_URL"]

    assert "8768:8768" in app["ports"]
    assert "postgres_data" in compose["volumes"]


def test_reverse_proxy_profiles_reference_existing_configs():
    compose = load_compose()

    nginx = compose["services"]["nginx"]
    assert "80:80" in nginx["ports"]
    assert "443:443" in nginx["ports"]

    mounted_files = [
        v.split(":", 1)[0].removeprefix("./") for v in nginx.get("volumes", [])
    ]
    for relative in mounted_files:
        if relative and not relative.startswith(("certs", "openglaze_")):
            assert (ROOT / relative).exists(), f"compose references missing {relative}"


def test_tls_reverse_proxy_documents_expected_certificate_files():
    tls_config = (ROOT / "nginx.tls.conf").read_text()
    docs = (ROOT / "docs/self-hosting.md").read_text()

    assert "/etc/nginx/certs/fullchain.pem" in tls_config
    assert "/etc/nginx/certs/privkey.pem" in tls_config
    assert "certs/fullchain.pem" in docs
    assert "certs/privkey.pem" in docs


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


def test_runtime_ports_and_cors_defaults_match_documented_docker_port():
    server = (ROOT / "server.py").read_text()
    readme = (ROOT / "README.md").read_text()

    assert "http://localhost:8768" in readme
    assert "Open http://localhost:8768" in readme
    assert "localhost:8767" not in server
    assert "FLASK_PORT" in server
    assert "configured_port" in server


def test_experimental_cloud_env_names_postgres_host():
    env = (ROOT / ".env.example").read_text()
    assert "POSTGRES_PASSWORD" in env


def test_codecov_action_uses_v6_input_name():
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "codecov/codecov-action@v6" in ci
    assert "files: ./coverage.xml" in ci
    assert "file: ./coverage.xml" not in ci


def test_app_serves_docs_discovery_assets():
    server = (ROOT / "server.py").read_text()
    assert 'send_from_directory("docs"' in server
    assert '"/llms.txt"' in server
    assert '"/sitemap.xml"' in server
    assert '"/social-preview.png"' in server


def test_kyanite_domain_is_canonical_public_host():
    canonical = "https://openglaze.kyanitelabs.tech"
    checked = [
        ROOT / "README.md",
        ROOT / "docs/llms.txt",
        ROOT / "docs/llms-full.txt",
        ROOT / "docs/ai.txt",
        ROOT / "docs/sitemap.xml",
        ROOT / "tests/test_seo_contracts.py",
    ]
    for path in checked:
        content = path.read_text()
        assert canonical in content, f"{path} does not reference canonical host"
        assert "pastorsimon1798.github.io/openglaze" not in content


def test_app_serves_sitemap_markdown_html_aliases():
    server = (ROOT / "server.py").read_text()
    sitemap = (ROOT / "docs/sitemap.xml").read_text()

    for page in ["user-guide", "API", "self-hosting"]:
        assert f"/{page}.html" in sitemap
        assert (ROOT / f"docs/{page}.md").exists()

    assert "render_markdown_doc" in server
    assert 'Path("docs") / f"{Path(path).stem}.md"' in server
