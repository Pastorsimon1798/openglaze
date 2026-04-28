"""Tests for core CRUD routes — glazes, combinations, health, mode."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import json
from unittest.mock import patch


@pytest.fixture
def app(test_db_path):
    with patch.dict(
        "os.environ",
        {
            "DATABASE_PATH": test_db_path,
            "AI_PROVIDER": "lmstudio",
            "LM_STUDIO_URL": "http://127.0.0.1:1234/v1",
            "LM_STUDIO_MODEL": "test-model",
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


@pytest.fixture
def client(app):
    return app.test_client()


class TestHealthRoute:
    def test_health_returns_healthy(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "healthy"


class TestModeRoute:
    def test_mode_returns_personal(self, client):
        resp = client.get("/api/mode")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["mode"] == "personal"


class TestGlazeRoutes:
    def test_get_glazes_returns_list(self, client):
        resp = client.get("/api/glazes")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert len(data) == 3

    def test_get_single_glaze(self, client):
        resp = client.get("/api/glazes/glaze-1")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["name"] == "Chun Blue"

    def test_get_glaze_not_found(self, client):
        resp = client.get("/api/glazes/nonexistent")
        assert resp.status_code == 404

    def test_create_glaze(self, client):
        resp = client.post(
            "/api/glazes",
            data=json.dumps({"name": "Test Glaze", "family": "Greens", "hex": "#00ff00"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert "id" in data

    def test_create_glaze_no_data(self, client):
        resp = client.post("/api/glazes", content_type="application/json")
        assert resp.status_code == 400

    def test_update_glaze(self, client):
        resp = client.put(
            "/api/glazes/glaze-1",
            data=json.dumps({"name": "Updated Blue"}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_update_glaze_no_data(self, client):
        resp = client.put("/api/glazes/glaze-1", content_type="application/json")
        assert resp.status_code == 400

    def test_delete_glaze(self, client):
        resp = client.delete("/api/glazes/glaze-1")
        assert resp.status_code == 200
        resp2 = client.get("/api/glazes/glaze-1")
        assert resp2.status_code == 404


class TestCombinationRoutes:
    def test_get_combinations_returns_list(self, client):
        resp = client.get("/api/combinations")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_get_combinations_grouped(self, client):
        resp = client.get("/api/combinations/grouped")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, dict)

    def test_create_combination(self, client):
        resp = client.post(
            "/api/combinations",
            data=json.dumps({"base": "Chun Blue", "top": "Iron Red"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert "id" in data

    def test_create_combination_no_data(self, client):
        resp = client.post("/api/combinations", content_type="application/json")
        assert resp.status_code == 400

    def test_get_combination_by_id(self, client):
        # The seeded combination has id 1 (autoincrement)
        resp = client.get("/api/combinations/1")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["base"] == "Tenmoku"
        assert data["top"] == "Chun Blue"

    def test_get_combination_not_found(self, client):
        resp = client.get("/api/combinations/9999")
        assert resp.status_code == 404

    def test_update_combination(self, client):
        create_resp = client.post(
            "/api/combinations",
            data=json.dumps({"base": "Chun Blue", "top": "Iron Red"}),
            content_type="application/json",
        )
        combo_id = json.loads(create_resp.data)["id"]

        resp = client.put(
            f"/api/combinations/{combo_id}",
            data=json.dumps({"stage": "testing"}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_promote_combination(self, client):
        create_resp = client.post(
            "/api/combinations",
            data=json.dumps({"base": "Chun Blue", "top": "Iron Red"}),
            content_type="application/json",
        )
        combo_id = json.loads(create_resp.data)["id"]

        resp = client.post(
            f"/api/combinations/{combo_id}/promote",
            data=json.dumps({"result": "great combo"}),
            content_type="application/json",
        )
        assert resp.status_code == 200


class TestChemistryRoutes:
    def test_batch_analysis(self, client):
        resp = client.post(
            "/api/chemistry/batch",
            data=json.dumps({"cone": 10}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_scale_recipe(self, client):
        resp = client.post(
            "/api/chemistry/scale",
            data=json.dumps({
                "recipe": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
                "batch_size_grams": 5000,
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_scale_recipe_missing_fields(self, client):
        resp = client.post(
            "/api/chemistry/scale",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_compare_recipes(self, client):
        resp = client.post(
            "/api/chemistry/compare",
            data=json.dumps({
                "recipe_a": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
                "recipe_b": "Custer Feldspar 40, Silica 30, Whiting 15, EPK 15",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_compare_missing_recipe(self, client):
        resp = client.post(
            "/api/chemistry/compare",
            data=json.dumps({"recipe_a": "Silica 50"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_substitutions(self, client):
        resp = client.post(
            "/api/chemistry/substitutions",
            data=json.dumps({"material": "Custer Feldspar"}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_defects_analysis(self, client):
        resp = client.post(
            "/api/chemistry/defects",
            data=json.dumps({
                "recipe": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
                "defect": "crawling",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200


class TestDemoRoutes:
    def test_demo_glazes(self, client):
        resp = client.get("/api/demo/glazes")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)

    def test_demo_compatibility_missing_fields(self, client):
        resp = client.post(
            "/api/demo/compatibility",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400
