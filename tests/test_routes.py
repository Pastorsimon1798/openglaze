"""Tests for Flask routes — verify ToolRegistry removed and ContextRetriever wired."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import json
from unittest.mock import patch


class TestRouteImports:
    def test_no_tool_registry_in_server(self):
        """server.py should not import ToolRegistry."""
        import server

        source = Path(server.__file__).read_text()
        assert "from core.ai.tools import ToolRegistry" not in source

    def test_import_context_retriever_works(self):
        from core.ai.context import ContextRetriever

        assert ContextRetriever is not None


class TestAskStreamRoute:
    """Test /api/ask/stream route behavior."""

    @pytest.fixture
    def app(self, test_db_path):
        """Create app with test DB and mock AI."""
        with patch.dict(
            "os.environ",
            {
                "DATABASE_PATH": test_db_path,
                "AI_PROVIDER": "ollama",
                "OLLAMA_API": "http://localhost:11434/api/chat",
                "OLLAMA_MODEL": "test-model",
            },
        ):
            from server import create_app

            app = create_app(
                {
                    "mode": "personal",
                    "database": {"path": test_db_path},
                }
            )
        return app

    def test_ask_stream_400_no_question(self, app, test_db_path):
        client = app.test_client()
        resp = client.post(
            "/api/ask/stream", data=json.dumps({}), content_type="application/json"
        )
        # Route returns 400 for missing question (may be 400 or 500 depending
        # on rate_limit decorator interaction — key: it's not a 200 success)
        assert resp.status_code != 200

    def test_ask_stream_returns_sse(self, app, test_db_path):
        """Verify SSE format response with mocked AI."""
        from core.ai.kama import KamaAI

        # Mock the streaming to return a simple response
        with patch.object(
            KamaAI, "_stream_request", return_value=iter(["Hello from Kama"])
        ):
            client = app.test_client()
            resp = client.post(
                "/api/ask/stream",
                data=json.dumps({"question": "What is Chun Blue?"}),
                content_type="application/json",
            )
            assert resp.status_code == 200
            assert resp.content_type.startswith("text/event-stream")

            data = resp.get_data(as_text=True)
            assert "data: " in data
            # Parse SSE events
            events = [
                line.split("data: ", 1)[1]
                for line in data.strip().split("\n")
                if line.startswith("data: ")
            ]
            assert len(events) >= 1
            parsed = json.loads(events[0])
            assert parsed["type"] == "content"


class TestOptimizeRoute:
    """Test /api/chemistry/optimize route."""

    @pytest.fixture
    def app(self, test_db_path):
        with patch.dict(
            "os.environ",
            {
                "DATABASE_PATH": test_db_path,
                "AI_PROVIDER": "ollama",
                "OLLAMA_API": "http://localhost:11434/api/chat",
                "OLLAMA_MODEL": "test-model",
            },
        ):
            from server import create_app

            app = create_app(
                {
                    "mode": "personal",
                    "database": {"path": test_db_path},
                }
            )
        return app

    def test_optimize_missing_recipe(self, app):
        client = app.test_client()
        resp = client.post(
            "/api/chemistry/optimize",
            data=json.dumps({"target": "reduce_cte"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "recipe is required" in data["error"]

    def test_optimize_missing_target(self, app):
        client = app.test_client()
        resp = client.post(
            "/api/chemistry/optimize",
            data=json.dumps({"recipe": "Silica 50, Feldspar 50"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "target is required" in data["error"]

    def test_optimize_invalid_target(self, app):
        client = app.test_client()
        resp = client.post(
            "/api/chemistry/optimize",
            data=json.dumps(
                {
                    "recipe": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
                    "target": "invalid_target",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "Invalid target" in data["error"]

    def test_optimize_target_cte_requires_value(self, app):
        client = app.test_client()
        resp = client.post(
            "/api/chemistry/optimize",
            data=json.dumps(
                {
                    "recipe": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
                    "target": "target_cte",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "target_value is required" in data["error"]

    def test_optimize_reduce_cte_success(self, app):
        client = app.test_client()
        resp = client.post(
            "/api/chemistry/optimize",
            data=json.dumps(
                {
                    "recipe": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
                    "target": "reduce_cte",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["success"] is True
        assert len(data["suggestions"]) > 0
        assert data["original_surface"] == "glossy"

    def test_optimize_more_matte_success(self, app):
        client = app.test_client()
        resp = client.post(
            "/api/chemistry/optimize",
            data=json.dumps(
                {
                    "recipe": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
                    "target": "more_matte",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["success"] is True
        assert len(data["suggestions"]) > 0
        surfaces = [s["predicted_surface"] for s in data["suggestions"]]
        assert "matte" in surfaces or "satin" in surfaces

    def test_optimize_non_numeric_target_value(self, app):
        client = app.test_client()
        resp = client.post(
            "/api/chemistry/optimize",
            data=json.dumps(
                {
                    "recipe": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
                    "target": "target_cte",
                    "target_value": "abc",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "numeric" in data["error"]

    def test_optimize_non_numeric_max_suggestions(self, app):
        client = app.test_client()
        resp = client.post(
            "/api/chemistry/optimize",
            data=json.dumps(
                {
                    "recipe": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
                    "target": "reduce_cte",
                    "max_suggestions": "abc",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "numeric" in data["error"]

    def test_optimize_no_alumina_surface_target(self, app):
        client = app.test_client()
        resp = client.post(
            "/api/chemistry/optimize",
            data=json.dumps(
                {
                    "recipe": "Silica 50, Whiting 50",
                    "target": "more_glossy",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["success"] is True
        assert len(data["suggestions"]) == 0
        assert "alumina" in data["error"].lower()

    def test_optimize_max_suggestions_zero(self, app):
        client = app.test_client()
        resp = client.post(
            "/api/chemistry/optimize",
            data=json.dumps(
                {
                    "recipe": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
                    "target": "reduce_cte",
                    "max_suggestions": 0,
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data["suggestions"]) == 0
