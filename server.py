#!/usr/bin/env python3
"""
OpenGlaze - Unified Glaze Management Server
Supports both personal (single-user) and cloud (multi-tenant) modes.
Security-hardened as of March 2026.

Features:
- Mode detection (personal/cloud)
- Authentication (cloud mode)
- Rate limiting
- Security headers
- Per-user conversation memory
"""

import os
import json
import sqlite3
import logging
import secrets
from html import escape
from pathlib import Path
from typing import Optional

from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory,
    Response,
    stream_with_context,
    g,
)
from flask_cors import CORS

# Import configuration
from config import load_config, ConfigurationError

# Import security
from core.security import init_security, rate_limit, get_rate_limiter

# Import auth (cloud mode)
try:
    from core.auth import AuthMiddleware, get_current_user, get_user_id

    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    logging.getLogger(__name__).warning(
        "Auth module not available - cloud mode disabled"
    )

# Import core modules
from core.glazes import GlazeManager, Glaze
from core.combinations import CombinationManager, Combination
from core.experiments import ExperimentManager, Experiment
from core.ai import get_kama
from core.ai.context import ContextRetriever
from core.upload_utils import save_uploaded_file

try:
    from core.studios import StudioManager

    STUDIOS_AVAILABLE = True
except ImportError:
    STUDIOS_AVAILABLE = False

try:
    from core.gamification.manager import GamificationManager

    GAMIFICATION_AVAILABLE = True
except ImportError:
    GAMIFICATION_AVAILABLE = False

try:
    from core.predictions.manager import PredictionManager

    PREDICTIONS_AVAILABLE = True
except ImportError:
    PREDICTIONS_AVAILABLE = False

try:
    from core.templates import load_template, list_templates

    TEMPLATES_AVAILABLE = True
except ImportError:
    TEMPLATES_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Keep a reference to in-memory DB connections so they don't get garbage-collected
_memory_db_connections: dict = {}


def create_app(config: dict = None) -> Flask:
    """Create and configure the OpenGlaze Flask application."""
    app = Flask(__name__, static_folder="frontend")

    # Load configuration if not provided
    if config is None:
        try:
            config = load_config()
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            raise

    mode = config.get("mode")
    app.config["MODE"] = mode

    # Secret key for sessions
    secret_key = getattr(mode, "security", None)
    if secret_key:
        secret_key = secret_key.secret_key
    if not secret_key:
        secret_key = secrets.token_hex(32)
    app.config["SECRET_KEY"] = secret_key

    # Feature flags
    features = {
        "auth_enabled": getattr(mode, "AUTH_ENABLED", False),
        "multi_tenant": getattr(mode, "MULTI_TENANT", False),
        "api_access": getattr(mode, "API_ACCESS", False),
        "analytics": getattr(mode, "ANALYTICS", False),
    }
    app.config["FEATURES"] = features

    # CORS configuration
    configured_port = os.environ.get("FLASK_PORT", "8767")
    cors_origins = [
        f"http://localhost:{configured_port}",
        f"http://127.0.0.1:{configured_port}",
    ]
    extra_cors_origins = [
        origin.strip()
        for origin in os.environ.get("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]
    cors_origins.extend(extra_cors_origins)

    CORS(app, origins=cors_origins, supports_credentials=True)

    # Initialize security
    init_security(app)

    # Initialize auth middleware (cloud mode)
    if features["auth_enabled"] and AUTH_AVAILABLE:
        AuthMiddleware(app)
        logger.info("Authentication middleware enabled")

    # Database setup
    db_path = config.get("database", {}).get("path", "glaze.db")

    # Initialize database schema
    init_db(db_path)

    # Create managers (user_id is None for personal mode)
    @app.before_request
    def setup_managers():
        """Set up managers for each request."""
        user_id = get_user_id() if features["auth_enabled"] else None
        g.glaze_manager = GlazeManager(db_path, user_id=user_id)
        g.combo_manager = CombinationManager(db_path, user_id=user_id)
        g.exp_manager = ExperimentManager(db_path, user_id=user_id)
        g.context_retriever = ContextRetriever(db_path)
        # Shared DB connection for gamification/predictions (takes conn, not db_path)
        g.db_conn = get_db_connection(db_path)
        if GAMIFICATION_AVAILABLE:
            g.gamification_manager = GamificationManager(g.db_conn)
        if PREDICTIONS_AVAILABLE:
            g.prediction_manager = PredictionManager(g.db_conn)
        if STUDIOS_AVAILABLE:
            # For studio endpoints, user_id comes from simple auth or Ory
            from core.auth.middleware import get_user_id_or_simple

            studio_user_id = get_user_id_or_simple()
            g.studio_manager = StudioManager(db_path, user_id=studio_user_id)

    def require_auth_for_write():
        """Enforce authentication on write endpoints in cloud mode.

        Returns an error response if auth is required but user is not
        authenticated, or None if the request may proceed.
        """
        if not features["auth_enabled"] or not AUTH_AVAILABLE:
            return None
        try:
            user = get_current_user()
            if user:
                return None
        except Exception as e:
            logger.warning(f"Auth check failed: {e}")
        return jsonify({"error": "Authentication required"}), 401

    def get_current_user_id() -> Optional[str]:
        """Get current user ID (cloud mode only)."""
        if not features["auth_enabled"]:
            return None
        return get_user_id()

    # ==========================================
    # HEALTH CHECKS
    # ==========================================

    @app.route("/health")
    def health_check():
        """Basic health check."""
        return jsonify(
            {
                "status": "healthy",
                "mode": mode.name if hasattr(mode, "name") else "unknown",
                "version": "1.1.0",
            }
        )

    @app.route("/api/health")
    def api_health():
        """Detailed health check."""
        return jsonify(
            {
                "status": "healthy",
                "mode": mode.name if hasattr(mode, "name") else "unknown",
                "features": features,
                "rate_limit_stats": get_rate_limiter().get_stats(),
            }
        )

    # ==========================================
    # STATIC FILE ROUTES
    # ==========================================

    @app.route("/")
    def index():
        return send_from_directory("frontend", "index.html")

    def render_markdown_doc(markdown_path: Path):
        """Render repository markdown docs as simple crawlable HTML aliases."""
        source = markdown_path.read_text(encoding="utf-8")
        title = markdown_path.stem.replace("-", " ").title()
        body = []
        in_list = False
        in_code = False
        code_lines = []

        def close_list():
            nonlocal in_list
            if in_list:
                body.append("</ul>")
                in_list = False

        for raw_line in source.splitlines():
            line = raw_line.rstrip()
            if line.startswith("```"):
                if in_code:
                    body.append(
                        f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>"
                    )
                    code_lines = []
                    in_code = False
                else:
                    close_list()
                    in_code = True
                continue
            if in_code:
                code_lines.append(raw_line)
                continue
            if not line:
                close_list()
                continue
            if line.startswith("#"):
                close_list()
                level = min(len(line) - len(line.lstrip("#")), 6)
                text = line[level:].strip()
                if level == 1:
                    title = text
                body.append(f"<h{level}>{escape(text)}</h{level}>")
                continue
            if line.startswith(("- ", "* ")):
                if not in_list:
                    body.append("<ul>")
                    in_list = True
                body.append(f"<li>{escape(line[2:])}</li>")
                continue
            close_list()
            body.append(f"<p>{escape(line)}</p>")

        close_list()
        if in_code:
            body.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")

        canonical = f"https://openglaze.kyanitelabs.tech/{markdown_path.stem}.html"
        html = "\n".join(
            [
                "<!doctype html>",
                '<html lang="en">',
                "<head>",
                '<meta charset="utf-8">',
                '<meta name="viewport" content="width=device-width, initial-scale=1">',
                f"<title>{escape(title)} | OpenGlaze</title>",
                f'<link rel="canonical" href="{canonical}">',
                "</head>",
                "<body>",
                "<main>",
                *body,
                "</main>",
                "</body>",
                "</html>",
            ]
        )
        return Response(html, mimetype="text/html")

    @app.route("/llms.txt")
    @app.route("/llms-full.txt")
    @app.route("/ai.txt")
    @app.route("/robots.txt")
    @app.route("/sitemap.xml")
    @app.route("/social-preview.png")
    def docs_root_asset():
        return send_from_directory("docs", request.path.lstrip("/"))

    @app.route("/<path:path>")
    def static_files(path):
        # Don't serve hidden files or paths outside public static/docs directories
        if path.startswith(".") or ".." in path:
            return jsonify({"error": "Not found"}), 404
        if path.endswith((".html", ".txt", ".xml", ".png")):
            docs_file = Path("docs") / path
            if docs_file.is_file():
                return send_from_directory("docs", path)
            if path.endswith(".html"):
                markdown_file = Path("docs") / f"{Path(path).stem}.md"
                if markdown_file.is_file():
                    return render_markdown_doc(markdown_file)
        response = send_from_directory("frontend", path)
        if path == "sw.js":
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

    # ==========================================
    # MODE INFO ROUTE
    # ==========================================

    @app.route("/api/mode")
    def get_mode_info():
        """Get current mode information."""
        return jsonify(
            {
                "mode": mode.name if hasattr(mode, "name") else "personal",
                "features": features,
                "theme": getattr(mode, "DEFAULT_THEME", "dark"),
            }
        )

    # ==========================================
    # GLAZE API ROUTES
    # ==========================================

    @app.route("/api/glazes")
    @rate_limit(requests_per_minute=60)
    def get_glazes():
        """Get all glazes."""
        try:
            glazes = g.glaze_manager.get_all()
            return jsonify([glaze.to_dict() for glaze in glazes])
        except sqlite3.OperationalError as e:
            logger.error(f"Database error: {e}")
            return jsonify([])

    @app.route("/api/glazes/<glaze_id>")
    @rate_limit(requests_per_minute=60)
    def get_glaze(glaze_id: str):
        """Get a specific glaze."""
        glaze = g.glaze_manager.get_by_id(glaze_id)
        if glaze:
            return jsonify(glaze.to_dict())
        return jsonify({"error": "Glaze not found"}), 404

    @app.route("/api/glazes", methods=["POST"])
    @rate_limit(requests_per_minute=30)
    def create_glaze():
        """Create a new glaze."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err

        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        glaze = Glaze.from_dict(data)
        glaze_id = g.glaze_manager.create(glaze)
        return jsonify({"id": glaze_id}), 201

    @app.route("/api/glazes/<glaze_id>", methods=["PUT"])
    @rate_limit(requests_per_minute=30)
    def update_glaze(glaze_id: str):
        """Update a glaze."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err

        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        success = g.glaze_manager.update(glaze_id, data)
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Update failed"}), 400

    @app.route("/api/glazes/<glaze_id>", methods=["DELETE"])
    @rate_limit(requests_per_minute=30)
    def delete_glaze(glaze_id: str):
        """Delete a glaze."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err

        success = g.glaze_manager.delete(glaze_id)
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Delete failed"}), 400

    # ==========================================
    # COMBINATION API ROUTES
    # ==========================================

    @app.route("/api/combinations")
    @rate_limit(requests_per_minute=60)
    def get_combinations():
        """Get all combinations."""
        combo_type = request.args.get("type")
        if combo_type == "research-backed":
            combos = g.combo_manager.get_research_backed()
        elif combo_type == "user-prediction":
            combos = g.combo_manager.get_user_predictions()
        elif combo_type == "proven":
            combos = g.combo_manager.get_research_backed()  # backward compat
        elif combo_type == "hypothesis":
            combos = g.combo_manager.get_user_predictions()  # backward compat
        else:
            combos = g.combo_manager.get_all()
        return jsonify([c.to_dict() for c in combos])

    @app.route("/api/combinations/grouped")
    @rate_limit(requests_per_minute=60)
    def get_combinations_grouped():
        """Get combinations grouped by base glaze."""
        grouped = g.combo_manager.get_grouped_by_base()
        result = {}
        for base, combos in grouped.items():
            result[base] = [c.to_dict() for c in combos]
        return jsonify(result)

    @app.route("/api/combinations/<int:combo_id>")
    @rate_limit(requests_per_minute=60)
    def get_combination(combo_id: int):
        """Get a specific combination."""
        combo = g.combo_manager.get_by_id(combo_id)
        if combo:
            return jsonify(combo.to_dict())
        return jsonify({"error": "Combination not found"}), 404

    @app.route("/api/combinations", methods=["POST"])
    @rate_limit(requests_per_minute=30)
    def create_combination():
        """Create a new combination."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        combo = Combination.from_dict(data)

        # Check for Shino warning
        warning = g.combo_manager.check_shino_warning(combo.top, combo.base)
        if warning:
            logger.info(f"Shino warning for {combo.top} over {combo.base}")
            # Return warning but still create

        combo_id = g.combo_manager.create(combo)
        return jsonify({"id": combo_id, "warning": warning}), 201

    @app.route("/api/combinations/<int:combo_id>/promote", methods=["POST"])
    @rate_limit(requests_per_minute=30)
    def promote_combination(combo_id: int):
        """Promote a hypothesis to confirmed."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err
        data = request.json or {}
        result = data.get("result", "")
        success = g.combo_manager.promote_to_confirmed(combo_id, result)
        if success:
            # Gamification hooks
            user_id = get_current_user_id()
            if user_id and GAMIFICATION_AVAILABLE:
                g.gamification_manager.on_combination_tested(
                    user_id, combo_id, "proven"
                )
                g.gamification_manager.log_activity(
                    user_id, "combination_tested", {"combination_id": combo_id}
                )
            if user_id and PREDICTIONS_AVAILABLE:
                g.prediction_manager.resolve_predictions(combo_id, "proven")
            return jsonify({"success": True})
        return jsonify({"error": "Promotion failed"}), 400

    @app.route("/api/combinations/<int:combo_id>", methods=["PUT"])
    @rate_limit(requests_per_minute=30)
    def update_combination(combo_id: int):
        """Update a combination (stage, prediction_grade, etc.)."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        success = g.combo_manager.update(combo_id, data)
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Update failed"}), 400

    @app.route("/api/combinations/<int:combo_id>/simulate", methods=["POST"])
    @rate_limit(requests_per_minute=10)
    def simulate_combination(combo_id: int):
        """Run chemistry simulation for a single combo."""
        try:
            from core.simulation.runner import simulate_combo

            combo = g.combo_manager.get_by_id(combo_id)
            if not combo:
                return jsonify({"error": "Combination not found"}), 404

            base_glaze = g.glaze_manager.get_by_name(combo.base)
            top_glaze = g.glaze_manager.get_by_name(combo.top)

            prediction = simulate_combo(
                base_glaze=base_glaze,
                top_glaze=top_glaze,
                combo=combo,
                db_path=config.get("database", {}).get("path", "glaze.db"),
            )

            g.combo_manager.update(
                combo_id,
                {
                    "prediction_grade": prediction.get("prediction_grade", "unknown"),
                    "chemistry": prediction.get("chemistry_explanation"),
                    "result": prediction.get("predicted_result"),
                },
            )
            return jsonify(prediction)
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/combinations/simulate-all", methods=["POST"])
    @rate_limit(requests_per_minute=1)
    def simulate_all_combinations():
        """Run chemistry simulation for all unsimulated combos."""
        try:
            from core.simulation.batch_simulate import batch_simulate

            result = batch_simulate(
                db_path=config.get("database", {}).get("path", "glaze.db"),
                user_id=get_current_user_id() if features["auth_enabled"] else None,
            )
            return jsonify(result)
        except Exception as e:
            logger.error(f"Batch simulation error: {e}")
            return jsonify({"error": str(e)}), 500

    # ==========================================
    # CHEMISTRY / UMF API ROUTES
    # ==========================================

    @app.route("/api/glazes/<glaze_id>/umf")
    @rate_limit(requests_per_minute=60)
    def get_glaze_umf(glaze_id: str):
        """Calculate UMF for a specific glaze by ID or name.

        Query params:
            cone: Target firing cone (e.g., 6, 10). Defaults to 10.
        """
        try:
            from core.chemistry import calculate_umf
        except ImportError:
            return jsonify({"error": "Chemistry engine not available"}), 500

        glaze = g.glaze_manager.get_by_id(glaze_id)
        if not glaze:
            glaze = g.glaze_manager.get_by_name(glaze_id)
        if not glaze:
            return jsonify({"error": "Glaze not found"}), 404

        if not glaze.recipe:
            return jsonify(
                {
                    "success": False,
                    "error": "No recipe available",
                    "glaze_id": glaze_id,
                    "glaze_name": glaze.name,
                }
            )

        # Parse optional cone parameter
        cone_param = request.args.get("cone")
        cone = int(cone_param) if cone_param and cone_param.isdigit() else None

        result = calculate_umf(glaze.recipe, cone=cone)
        response = result.to_dict()
        response["glaze_id"] = glaze_id
        response["glaze_name"] = glaze.name
        return jsonify(response)

    @app.route("/api/combinations/<int:combo_id>/compatibility")
    @rate_limit(requests_per_minute=60)
    def get_combo_compatibility(combo_id: int):
        """Calculate compatibility for a specific combination.

        Query params:
            cone: Target firing cone (e.g., 6, 10). Defaults to 10.
        """
        try:
            from core.chemistry import CompatibilityAnalyzer
        except ImportError:
            return jsonify({"error": "Chemistry engine not available"}), 500

        combo = g.combo_manager.get_by_id(combo_id)
        if not combo:
            return jsonify({"error": "Combination not found"}), 404

        base_glaze = g.glaze_manager.get_by_name(combo.base)
        top_glaze = g.glaze_manager.get_by_name(combo.top)

        base_recipe = base_glaze.recipe if base_glaze else None
        top_recipe = top_glaze.recipe if top_glaze else None

        if not base_recipe and not top_recipe:
            return jsonify(
                {
                    "success": False,
                    "error": "One or both glazes have no recipe",
                    "base_recipe_available": bool(base_recipe),
                    "top_recipe_available": bool(top_recipe),
                }
            )

        # Parse optional cone parameter
        cone_param = request.args.get("cone")
        cone = int(cone_param) if cone_param and cone_param.isdigit() else None

        analyzer = CompatibilityAnalyzer()
        result = analyzer.analyze(
            base_recipe=base_recipe,
            top_recipe=top_recipe,
            base_name=combo.base or "",
            top_name=combo.top or "",
            cone=cone,
        )
        return jsonify(result.to_dict())

    @app.route("/api/chemistry/batch", methods=["POST"])
    @rate_limit(requests_per_minute=5)
    def batch_chemistry_analysis():
        """Run batch UMF and compatibility analysis for all glazes and combinations.

        Request body (optional):
            cone: Target firing cone for all analyses (default: 10)
        """
        data = request.json or {}
        cone = data.get("cone", 10)

        try:
            from core.chemistry import BatchAnalyzer
        except ImportError:
            return jsonify({"error": "Chemistry engine not available"}), 500

        try:
            analyzer = BatchAnalyzer(
                db_path=config.get("database", {}).get("path", "glaze.db"),
                user_id=get_current_user_id() if features["auth_enabled"] else None,
                cone=int(cone) if cone is not None else 10,
            )
            report = analyzer.generate_report()
            return jsonify(report)
        except Exception as e:
            logger.error(f"Batch chemistry analysis error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/chemistry/scale", methods=["POST"])
    @rate_limit(requests_per_minute=60)
    def scale_recipe():
        """Scale a glaze recipe to a target batch size."""
        data = request.json or {}
        recipe = data.get("recipe")
        batch_size = data.get("batch_size_grams")
        unit = data.get("unit", "grams")

        if not recipe or not batch_size:
            return jsonify({"error": "recipe and batch_size_grams are required"}), 400

        try:
            from core.chemistry.batch import calculate_batch

            result = calculate_batch(recipe, float(batch_size), unit)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Recipe scaling error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/chemistry/compare", methods=["POST"])
    @rate_limit(requests_per_minute=60)
    def compare_glaze_recipes():
        """Compare two glaze recipes chemically.

        Request body:
            recipe_a: First recipe string
            recipe_b: Second recipe string
            name_a: Name for first recipe (optional)
            name_b: Name for second recipe (optional)
            cone: Target firing cone (optional, default 10)
        """
        data = request.json or {}
        recipe_a = data.get("recipe_a", "")
        recipe_b = data.get("recipe_b", "")
        name_a = data.get("name_a", "Recipe A")
        name_b = data.get("name_b", "Recipe B")
        cone = data.get("cone", 10)

        if not recipe_a or not recipe_b:
            return jsonify({"error": "recipe_a and recipe_b are required"}), 400

        try:
            from core.chemistry import compare_recipes

            result = compare_recipes(
                recipe_a,
                recipe_b,
                name_a=name_a,
                name_b=name_b,
                cone=int(cone) if cone is not None else 10,
            )
            return jsonify(result.to_dict())
        except Exception as e:
            logger.error(f"Recipe comparison error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/chemistry/optimize", methods=["POST"])
    @rate_limit(requests_per_minute=60)
    def optimize_glaze_recipe():
        """Optimize a glaze recipe to hit target properties.

        Request body:
            recipe: Recipe string (e.g. "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12")
            target: One of 'target_cte', 'reduce_cte', 'increase_cte',
                    'more_matte', 'more_glossy', 'reduce_alkali', 'reduce_running'
            target_value: Required for 'target_cte' (e.g. 6.5), optional hint for others
            max_suggestions: Number of suggestions to return (default 5)
        """
        data = request.json or {}
        recipe = data.get("recipe", "")
        target = data.get("target", "")
        target_value = data.get("target_value")
        max_suggestions = data.get("max_suggestions", 5)

        if not recipe:
            return jsonify({"error": "recipe is required"}), 400
        if not target:
            return jsonify({"error": "target is required"}), 400

        valid_targets = {
            "target_cte",
            "reduce_cte",
            "increase_cte",
            "more_matte",
            "more_glossy",
            "reduce_alkali",
            "reduce_running",
        }
        if target not in valid_targets:
            return (
                jsonify(
                    {
                        "error": f"Invalid target. Must be one of: {', '.join(sorted(valid_targets))}"
                    }
                ),
                400,
            )

        if target == "target_cte" and target_value is None:
            return jsonify({"error": "target_value is required for target_cte"}), 400

        try:
            tv = float(target_value) if target_value is not None else None
            ms = int(max_suggestions)
        except (ValueError, TypeError):
            return (
                jsonify({"error": "target_value and max_suggestions must be numeric"}),
                400,
            )

        try:
            from core.chemistry import optimize_recipe

            result = optimize_recipe(
                recipe,
                target,
                target_value=tv,
                max_suggestions=ms,
            )
            return jsonify(result.to_dict())
        except Exception as e:
            logger.error(f"Recipe optimization error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/chemistry/substitutions", methods=["POST"])
    @rate_limit(requests_per_minute=60)
    def get_substitutions():
        """Get material substitution suggestions for a recipe.

        Request body:
            recipe: Recipe string or object
            material: Specific material name to find substitutes for (optional)
        """
        data = request.json or {}
        recipe = data.get("recipe", "")
        material = data.get("material", "")

        if not recipe and not material:
            return jsonify({"error": "recipe or material is required"}), 400

        try:
            from core.chemistry import SubstitutionEngine

            engine = SubstitutionEngine()

            if material:
                # Single material lookup
                suggestions = engine.suggest(material)
                return jsonify(
                    {
                        "success": True,
                        "material": material,
                        "suggestions": [
                            {
                                "original": s.original,
                                "substitute": s.substitute,
                                "ratio": s.ratio,
                                "confidence": s.confidence,
                                "notes": s.notes,
                                "chemistry_impact": s.chemistry_impact,
                            }
                            for s in suggestions
                        ],
                    }
                )
            else:
                # Full recipe analysis
                from core.chemistry import suggest_substitutions

                result = suggest_substitutions(recipe)
                return jsonify(result.to_dict())
        except Exception as e:
            logger.error(f"Substitution error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/chemistry/defects", methods=["POST"])
    @rate_limit(requests_per_minute=60)
    def predict_glaze_defects():
        """Predict potential defects for a glaze recipe.

        Request body:
            recipe: Recipe string or object
            cone: Target firing cone (optional, default 10)
            clay_body_cte: CTE of clay body in ×10⁻⁶/°C (optional)
        """
        data = request.json or {}
        recipe = data.get("recipe", "")
        cone = data.get("cone", 10)
        clay_body_cte = data.get("clay_body_cte")

        if not recipe:
            return jsonify({"error": "recipe is required"}), 400

        try:
            from core.chemistry import predict_defects

            result = predict_defects(
                recipe,
                cone=int(cone) if cone is not None else 10,
                clay_body_cte=(
                    float(clay_body_cte) if clay_body_cte is not None else None
                ),
            )
            return jsonify(result.to_dict())
        except Exception as e:
            logger.error(f"Defect prediction error: {e}")
            return jsonify({"error": str(e)}), 500

    # ==========================================
    # EXPERIMENT API ROUTES
    # ==========================================

    @app.route("/api/experiments")
    @rate_limit(requests_per_minute=60)
    def get_experiments():
        """Get all experiments."""
        stage = request.args.get("stage")
        if stage:
            experiments = g.exp_manager.get_by_stage(stage)
        else:
            experiments = g.exp_manager.get_all()
        return jsonify([e.to_dict() for e in experiments])

    @app.route("/api/experiments/active")
    @rate_limit(requests_per_minute=60)
    def get_active_experiments():
        """Get active experiments."""
        experiments = g.exp_manager.get_active()
        return jsonify([e.to_dict() for e in experiments])

    @app.route("/api/experiments/stats")
    @rate_limit(requests_per_minute=60)
    def get_experiment_stats():
        """Get experiment pipeline statistics."""
        stats = g.exp_manager.get_pipeline_stats()
        return jsonify(stats)

    @app.route("/api/experiments/<int:exp_id>")
    @rate_limit(requests_per_minute=60)
    def get_experiment(exp_id: int):
        """Get a specific experiment."""
        exp = g.exp_manager.get_by_id(exp_id)
        if exp:
            return jsonify(exp.to_dict())
        return jsonify({"error": "Experiment not found"}), 404

    @app.route("/api/experiments", methods=["POST"])
    @rate_limit(requests_per_minute=30)
    def create_experiment():
        """Create a new experiment."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        exp = Experiment.from_dict(data)
        exp_id = g.exp_manager.create(exp)
        return jsonify({"id": exp_id}), 201

    @app.route("/api/experiments/<int:exp_id>/advance", methods=["POST"])
    @rate_limit(requests_per_minute=30)
    def advance_experiment(exp_id: int):
        """Advance experiment to next stage."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err
        success = g.exp_manager.advance_stage(exp_id)
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Advance failed"}), 400

    @app.route("/api/experiments/<int:exp_id>/result", methods=["POST"])
    @rate_limit(requests_per_minute=30)
    def record_experiment_result(exp_id: int):
        """Record experiment result."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err
        data = request.json or {}
        result = data.get("result", "")
        rating = data.get("rating")
        photo = data.get("photo")
        success = g.exp_manager.record_result(exp_id, result, rating, photo)
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Record failed"}), 400

    @app.route("/api/experiments/<int:exp_id>/archive", methods=["POST"])
    @rate_limit(requests_per_minute=30)
    def archive_experiment(exp_id: int):
        """Archive an experiment."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err
        data = request.json or {}
        archive_type = data.get("type", "successful")
        success = g.exp_manager.archive(exp_id, archive_type)
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Archive failed"}), 400

    # ==========================================
    # UPLOAD & PHOTOS API ROUTES
    # ==========================================

    @app.route("/api/upload", methods=["POST"])
    @rate_limit(requests_per_minute=20)
    def upload_photo():
        """Upload a photo file. Accepts multipart/form-data with 'photo' field."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err
        if "photo" not in request.files:
            return jsonify({"error": "No photo field in upload"}), 400

        file = request.files["photo"]
        if not file or not file.filename:
            return jsonify({"error": "No file provided"}), 400
        try:
            relative_path = save_uploaded_file(
                file, os.path.join("frontend", "uploads")
            )
            return jsonify(
                {"success": True, "path": relative_path, "url": f"/{relative_path}"}
            )
        except (ValueError, OverflowError) as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return jsonify({"error": "Upload failed"}), 500

    @app.route("/api/photos", methods=["GET"])
    @rate_limit(requests_per_minute=60)
    def get_photos():
        """Return all experiments that have a photo attached."""
        photos = g.exp_manager.get_all_with_photos()
        return jsonify({"photos": photos})

    # ==========================================
    # AI (KAMA) API ROUTES
    # ==========================================

    @app.route("/api/ask/stream", methods=["POST"])
    @rate_limit(requests_per_minute=10)  # Lower limit for AI
    def ask_ai_stream():
        """Stream AI responses using Server-Sent Events."""
        data = request.json or {}
        question = data.get("question", "")
        clear = data.get("clear", False)
        images = data.get("images")

        if not question:
            return jsonify({"error": "No question provided"}), 400

        # Get session/user for conversation isolation
        session_id = request.cookies.get("session_id")
        user_id = get_current_user_id() if features["auth_enabled"] else None

        def generate():
            try:
                kama = get_kama()
                if clear:
                    kama.clear_conversation(session_id, user_id)
                for event in kama.ask_stream_with_context(
                    question,
                    context_retriever=g.context_retriever,
                    session_id=session_id,
                    user_id=user_id,
                    images=images,
                ):
                    yield f"data: {json.dumps(event)}\n\n"
            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"AI stream backend unavailable: {e}")
                yield f"data: {json.dumps({'type': 'error', 'ai_available': False, 'content': 'AI backend unavailable. Please ensure LM Studio is running or configure ANTHROPIC_API_KEY.'})}\n\n"
            except Exception as e:
                logger.error(f"AI stream error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.route("/api/ask", methods=["POST"])
    @rate_limit(requests_per_minute=10)  # Lower limit for AI
    def ask_ai():
        """Ask Kama a question (non-streaming)."""
        data = request.json or {}
        question = data.get("question", "")
        clear = data.get("clear", False)
        images = data.get("images")

        if not question:
            return jsonify({"error": "No question provided"}), 400

        try:
            # Get session/user for conversation isolation
            session_id = request.cookies.get("session_id")
            user_id = get_current_user_id() if features["auth_enabled"] else None

            from core.ai import ask_kama

            response = ask_kama(
                question,
                clear=clear,
                session_id=session_id,
                user_id=user_id,
                images=images,
            )
            return jsonify({"response": response})

        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"AI backend unavailable: {e}")
            return (
                jsonify(
                    {
                        "ai_available": False,
                        "error": "AI backend unavailable",
                        "message": "The AI assistant is currently offline. Please ensure Ollama is running or configure a cloud AI provider (ANTHROPIC_API_KEY).",
                        "help": "For LM Studio: open LM Studio and start a local server on port 1234. For Ollama: run 'ollama serve'. For cloud: set ANTHROPIC_API_KEY.",
                    }
                ),
                503,
            )
        except Exception as e:
            logger.error(f"AI error: {e}")
            return jsonify({"error": str(e)}), 500

    # ==========================================
    # INBOX API ROUTES
    # ==========================================

    @app.route("/api/inbox", methods=["GET"])
    @rate_limit(requests_per_minute=60)
    def get_inbox():
        """Get inbox items."""
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        user_id = get_current_user_id()
        if user_id:
            cursor.execute(
                "SELECT * FROM inbox WHERE user_id = ? OR user_id IS NULL", (user_id,)
            )
        else:
            cursor.execute("SELECT * FROM inbox WHERE user_id IS NULL")

        rows = cursor.fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows])

    @app.route("/api/inbox", methods=["POST"])
    @rate_limit(requests_per_minute=30)
    def add_to_inbox():
        """Add idea to inbox."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err
        data = request.json or {}
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO inbox (base, top, notes, user_id) VALUES (?, ?, ?, ?)",
            (
                data.get("base"),
                data.get("top"),
                data.get("notes"),
                get_current_user_id(),
            ),
        )
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()

        return jsonify({"id": last_id}), 201

    # ==========================================
    # SIMPLE AUTH ROUTES
    # ==========================================

    @app.route("/api/auth/simple-login", methods=["POST"])
    @rate_limit(requests_per_minute=10)
    def simple_login():
        """Login with display name — returns token."""
        if not STUDIOS_AVAILABLE:
            return jsonify({"error": "Studios not available"}), 503

        data = request.json or {}
        display_name = (data.get("display_name") or "").strip()
        if not display_name or len(display_name) > 50:
            return jsonify({"error": "Display name is required (max 50 chars)"}), 400

        from core.auth.simple_auth import create_session

        session = create_session(display_name)
        return jsonify(session)

    @app.route("/api/auth/me")
    def auth_me():
        """Get current user info from simple auth or Ory."""
        from core.auth.middleware import get_simple_user

        simple = get_simple_user()
        if simple:
            return jsonify(simple)

        user = get_current_user()
        if user:
            return jsonify(
                {
                    "user_id": user["user_id"],
                    "display_name": user.get("email", user.get("display_name", "")),
                }
            )

        return jsonify({"error": "Not authenticated"}), 401

    # ==========================================
    # STUDIO API ROUTES
    # ==========================================

    def _get_studio_user():
        """Get user_id and display_name for studio operations."""
        from core.auth.middleware import get_simple_user

        simple = get_simple_user()
        if simple:
            return simple["user_id"], simple["display_name"]
        user = get_current_user()
        if user:
            return user["user_id"], user.get("email", user.get("display_name", ""))
        return None, None

    @app.route("/api/studios", methods=["POST"])
    @rate_limit(requests_per_minute=10)
    def create_studio():
        """Create a new studio."""
        if not STUDIOS_AVAILABLE:
            return jsonify({"error": "Studios not available"}), 503

        user_id, display_name = _get_studio_user()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        data = request.json or {}
        name = (data.get("name") or "").strip()
        if not name or len(name) > 100:
            return jsonify({"error": "Studio name is required (max 100 chars)"}), 400

        studio = g.studio_manager.create_studio(name, display_name)
        return jsonify(studio), 201

    @app.route("/api/studios/join", methods=["POST"])
    @rate_limit(requests_per_minute=10)
    def join_studio():
        """Join a studio by invite code."""
        if not STUDIOS_AVAILABLE:
            return jsonify({"error": "Studios not available"}), 503

        user_id, display_name = _get_studio_user()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        data = request.json or {}
        invite_code = (data.get("invite_code") or "").strip().upper()
        if not invite_code:
            return jsonify({"error": "Invite code is required"}), 400

        dn = (data.get("display_name") or display_name).strip()
        studio = g.studio_manager.join_by_code(invite_code, dn, user_id)
        if not studio:
            return jsonify({"error": "Invalid invite code"}), 404

        return jsonify(studio)

    @app.route("/api/studios")
    def list_studios():
        """List studios the user belongs to."""
        if not STUDIOS_AVAILABLE:
            return jsonify([])

        user_id, _ = _get_studio_user()
        if not user_id:
            return jsonify([])

        studios = g.studio_manager.get_user_studios(user_id)
        return jsonify(studios)

    @app.route("/api/studios/<studio_id>")
    def get_studio_detail(studio_id):
        """Get studio details + members."""
        if not STUDIOS_AVAILABLE:
            return jsonify({"error": "Not available"}), 503

        studio = g.studio_manager.get_studio(studio_id)
        if not studio:
            return jsonify({"error": "Studio not found"}), 404

        members = g.studio_manager.get_members(studio_id)
        return jsonify(
            {
                **studio.to_dict(),
                "members": [m.to_dict() for m in members],
            }
        )

    @app.route("/api/studios/<studio_id>/regenerate-code", methods=["POST"])
    def regenerate_invite(studio_id):
        """Admin: regenerate invite code."""
        if not STUDIOS_AVAILABLE:
            return jsonify({"error": "Not available"}), 503

        user_id, _ = _get_studio_user()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        new_code = g.studio_manager.regenerate_invite_code(studio_id, user_id)
        if not new_code:
            return jsonify({"error": "Only admins can regenerate invite codes"}), 403

        return jsonify({"invite_code": new_code})

    @app.route("/api/studios/<studio_id>", methods=["DELETE"])
    def delete_studio(studio_id):
        """Admin: delete studio."""
        if not STUDIOS_AVAILABLE:
            return jsonify({"error": "Not available"}), 503

        user_id, _ = _get_studio_user()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        if g.studio_manager.delete_studio(studio_id, user_id):
            return jsonify({"success": True})
        return jsonify({"error": "Only admins can delete studios"}), 403

    # ==========================================
    # LAB QUEUE ROUTES
    # ==========================================

    @app.route("/api/studios/<studio_id>/lab-queue")
    def get_lab_queue(studio_id):
        """Get testable combos with claim status."""
        if not STUDIOS_AVAILABLE:
            return jsonify([])

        queue = g.studio_manager.get_lab_queue(studio_id)
        return jsonify(queue)

    @app.route(
        "/api/studios/<studio_id>/lab-queue/<int:combo_id>/claim", methods=["POST"]
    )
    def claim_combo(studio_id, combo_id):
        """Claim a combo for testing."""
        if not STUDIOS_AVAILABLE:
            return jsonify({"error": "Not available"}), 503

        user_id, display_name = _get_studio_user()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        assignment = g.studio_manager.claim_combo(
            studio_id, combo_id, user_id, display_name
        )
        if not assignment:
            return jsonify({"error": "Already claimed by someone else"}), 409

        return jsonify(assignment.to_dict()), 201

    @app.route(
        "/api/studios/<studio_id>/lab-queue/<int:combo_id>/release", methods=["POST"]
    )
    def release_combo(studio_id, combo_id):
        """Release a claimed combo."""
        if not STUDIOS_AVAILABLE:
            return jsonify({"error": "Not available"}), 503

        if g.studio_manager.release_combo(studio_id, combo_id):
            return jsonify({"success": True})
        return jsonify({"error": "Not claimed or already released"}), 404

    @app.route("/api/studios/<studio_id>/my-claims")
    def get_my_claims(studio_id):
        """Get combos claimed by current user."""
        if not STUDIOS_AVAILABLE:
            return jsonify([])

        user_id, _ = _get_studio_user()
        if not user_id:
            return jsonify([])

        claims = g.studio_manager.get_my_claims(studio_id, user_id)
        return jsonify([c.to_dict() for c in claims])

    # ==========================================
    # FIRING LOG ROUTES
    # ==========================================

    @app.route("/api/experiments/<int:exp_id>/firing-log", methods=["POST"])
    def submit_firing_log(exp_id):
        """Submit a firing log for an experiment."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err
        data = request.json or {}
        try:
            success = g.exp_manager.log_firing_result(exp_id, data)
            if not success:
                return jsonify({"error": "Experiment not found"}), 404
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Update combo prediction grade if confirmation provided
        confirmation = data.get("confirmation")
        exp = g.exp_manager.get_by_id(exp_id)
        if exp and exp.combination_id and confirmation in ("confirmed", "surprise"):
            g.combo_manager.update(
                exp.combination_id,
                {
                    "prediction_grade": confirmation,
                    "type": confirmation,
                },
            )

            # Complete any lab claim
            if data.get("studio_id") and STUDIOS_AVAILABLE:
                g.studio_manager.complete_claim(
                    data["studio_id"], exp.combination_id, exp_id
                )

        return jsonify({"success": True})

    @app.route("/api/experiments/<int:exp_id>/share", methods=["POST"])
    def share_experiment(exp_id):
        """Share experiment result with studio."""
        auth_err = require_auth_for_write()
        if auth_err:
            return auth_err
        if not STUDIOS_AVAILABLE:
            return jsonify({"error": "Not available"}), 503

        data = request.json or {}
        studio_id = data.get("studio_id")
        if not studio_id:
            return jsonify({"error": "studio_id is required"}), 400

        if g.exp_manager.share_with_studio(exp_id, studio_id):
            return jsonify({"success": True})
        return jsonify({"error": "Experiment not found"}), 404

    @app.route("/api/studios/<studio_id>/experiments")
    def get_studio_experiments(studio_id):
        """Get all experiments shared with a studio."""
        experiments = g.exp_manager.get_studio_experiments(studio_id)
        return jsonify([e.to_dict() for e in experiments])

    # ==========================================
    # DEMO API ROUTES (public, no auth)
    # ==========================================

    def _load_demo_glazes():
        """Load curated demo glazes from ceramics-foundation data."""
        try:
            demo_path = (
                Path(__file__).resolve().parent
                / "ceramics-foundation"
                / "data"
                / "demo-glazes.json"
            )
            if not demo_path.exists():
                # Try alternate location
                demo_path = (
                    Path(__file__).resolve().parent.parent
                    / "ceramics-foundation"
                    / "data"
                    / "demo-glazes.json"
                )
            if demo_path.exists():
                with open(demo_path, "r") as f:
                    data = json.load(f)
                    return data.get("glazes", [])
        except Exception as e:
            logger.debug(f"Could not load demo glazes: {e}")
        return []

    def _get_demo_glaze_by_name(name: str):
        """Find a demo glaze by name (case-insensitive)."""
        demos = _load_demo_glazes()
        name_lower = name.lower().strip()
        for demo in demos:
            if (
                demo.get("name", "").lower().strip() == name_lower
                or demo.get("id", "").lower().strip() == name_lower
            ):
                return demo
        return None

    @app.route("/api/demo/glazes")
    def get_demo_glazes():
        """Get curated demo glazes — real, open-source reference formulations."""
        try:
            glazes = _load_demo_glazes()
            if glazes:
                return jsonify(glazes)
            # Fallback to DB if demo file unavailable
            conn = g.db_conn
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM glazes LIMIT 5")
            rows = cursor.fetchall()
            return jsonify([dict(row) for row in rows])
        except Exception as e:
            logger.error(f"Demo glazes error: {e}")
            return jsonify([])

    @app.route("/api/demo/compatibility", methods=["POST"])
    def check_demo_compatibility():
        """Check compatibility between two glazes (public endpoint).

        Works with demo glaze names from the curated collection.
        """
        data = request.json or {}
        glaze_a_name = data.get("glaze_a")
        glaze_b_name = data.get("glaze_b")
        cone = data.get("cone", 10)
        if not glaze_a_name or not glaze_b_name:
            return jsonify({"error": "Both glaze_a and glaze_b are required"}), 400

        try:
            # Try demo glazes first
            demo_a = _get_demo_glaze_by_name(glaze_a_name)
            demo_b = _get_demo_glaze_by_name(glaze_b_name)

            if demo_a and demo_b and demo_a.get("recipe") and demo_b.get("recipe"):
                from core.chemistry import CompatibilityAnalyzer

                analyzer = CompatibilityAnalyzer()
                result = analyzer.analyze(
                    base_recipe=demo_a["recipe"],
                    top_recipe=demo_b["recipe"],
                    base_name=demo_a.get("name", glaze_a_name),
                    top_name=demo_b.get("name", glaze_b_name),
                    cone=(
                        int(cone)
                        if isinstance(cone, (int, str)) and str(cone).isdigit()
                        else 10
                    ),
                )
                return jsonify(result.to_dict())

            # Fallback to DB-based compatibility
            result = compute_compatibility(glaze_a_name, glaze_b_name, db_path=db_path)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Compatibility check error: {e}")
            return jsonify({"error": str(e)}), 500

    # ==========================================
    # PREDICTIONS API ROUTES (auth required)
    # ==========================================

    @app.route("/api/predictions", methods=["POST"])
    @rate_limit(requests_per_minute=30)
    def create_prediction():
        """Create a prediction for a combination."""
        if not PREDICTIONS_AVAILABLE:
            return jsonify({"error": "Predictions not available"}), 503

        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        data = request.json or {}
        combo_id = data.get("combo_id")
        predicted_outcome = data.get("predicted_outcome", "")
        confidence = data.get("confidence", 50)

        if not combo_id or not predicted_outcome:
            return jsonify({"error": "combo_id and predicted_outcome are required"}), 400

        try:
            result = g.prediction_manager.create_prediction(
                user_id, combo_id, predicted_outcome, confidence
            )
            return jsonify(result), 201
        except Exception as e:
            logger.error(f"Create prediction error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/predictions/leaderboard")
    @rate_limit(requests_per_minute=60)
    def get_prediction_leaderboard():
        """Get prediction leaderboard (user vs AI)."""
        if not PREDICTIONS_AVAILABLE:
            return jsonify({"error": "Predictions not available"}), 503

        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        try:
            leaderboard = g.prediction_manager.get_leaderboard(user_id)
            return jsonify(leaderboard)
        except Exception as e:
            logger.error(f"Leaderboard error: {e}")
            return jsonify({"error": str(e)}), 500

    # ==========================================
    # GAMIFICATION API ROUTES (auth required)
    # ==========================================

    @app.route("/api/stats")
    @rate_limit(requests_per_minute=60)
    def get_user_stats():
        """Get user gamification stats and badges."""
        if not GAMIFICATION_AVAILABLE:
            return jsonify({"error": "Gamification not available"}), 503

        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        try:
            stats = g.gamification_manager.get_stats(user_id)
            badges = g.gamification_manager.get_badges(user_id)
            return jsonify(
                {
                    "stats": stats.to_dict() if stats else None,
                    "badges": [b.to_dict() for b in badges] if badges else [],
                }
            )
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/progress")
    @rate_limit(requests_per_minute=60)
    def get_progress():
        """Get user progress — combo counts + gamification stats."""
        if not GAMIFICATION_AVAILABLE:
            return jsonify({"error": "Gamification not available"}), 503

        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        try:
            conn = g.db_conn
            cursor = conn.cursor()

            # Combo counts
            cursor.execute(
                "SELECT COUNT(*) FROM combinations WHERE user_id = ?", (user_id,)
            )
            total_combos = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM combinations WHERE user_id = ? AND stage IN ('tested', 'proven', 'confirmed')",
                (user_id,),
            )
            tested_combos = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM combinations WHERE user_id = ? AND type = 'research-backed'",
                (user_id,),
            )
            research_combos = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM combinations WHERE user_id = ? AND type = 'user-prediction'",
                (user_id,),
            )
            prediction_combos = cursor.fetchone()[0]

            # Stage breakdown
            cursor.execute(
                "SELECT stage, COUNT(*) FROM combinations WHERE user_id = ? GROUP BY stage",
                (user_id,),
            )
            stage_breakdown = dict(cursor.fetchall())

            # Gamification stats
            stats = g.gamification_manager.get_stats(user_id)

            return jsonify(
                {
                    "total_combos": total_combos,
                    "tested_combos": tested_combos,
                    "research_combos": research_combos,
                    "prediction_combos": prediction_combos,
                    "stage_breakdown": stage_breakdown,
                    "stats": stats.to_dict() if stats else None,
                }
            )
        except Exception as e:
            logger.error(f"Progress error: {e}")
            return jsonify({"error": str(e)}), 500

    # ==========================================
    # TEMPLATES API ROUTES (mixed auth)
    # ==========================================

    @app.route("/api/templates")
    def get_templates():
        """List available templates."""
        if not TEMPLATES_AVAILABLE:
            return jsonify({"error": "Templates not available"}), 503
        try:
            templates = list_templates()
            return jsonify(templates)
        except Exception as e:
            logger.error(f"List templates error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/templates/<template_id>")
    def get_template(template_id):
        """Get a specific template by ID."""
        if not TEMPLATES_AVAILABLE:
            return jsonify({"error": "Templates not available"}), 503
        try:
            template = load_template(template_id)
            if template:
                return jsonify(template)
            return jsonify({"error": "Template not found"}), 404
        except Exception as e:
            logger.error(f"Load template error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/templates/<template_id>/apply", methods=["POST"])
    @rate_limit(requests_per_minute=10)
    def apply_template(template_id):
        """Apply a template — insert glazes into user's account."""
        if not TEMPLATES_AVAILABLE:
            return jsonify({"error": "Templates not available"}), 503

        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        try:
            template = load_template(template_id)
            if not template:
                return jsonify({"error": "Template not found"}), 404

            conn = g.db_conn
            cursor = conn.cursor()
            inserted = 0

            for glaze in template.get("glazes", []):
                glaze_id = glaze.get("id", f"{template_id}-{inserted}")
                cursor.execute(
                    """INSERT OR IGNORE INTO glazes
                    (id, name, family, hex, chemistry, behavior, layering, warning, recipe, catalog_code, food_safe, notes, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        glaze_id,
                        glaze.get("name"),
                        glaze.get("family"),
                        glaze.get("hex"),
                        glaze.get("chemistry"),
                        glaze.get("behavior"),
                        glaze.get("layering"),
                        glaze.get("warning"),
                        glaze.get("recipe"),
                        glaze.get("catalog_code"),
                        glaze.get("food_safe"),
                        glaze.get("notes"),
                        user_id,
                    ),
                )
                if cursor.rowcount > 0:
                    inserted += 1

            conn.commit()
            return jsonify(
                {"inserted": inserted, "total": len(template.get("glazes", []))}
            )
        except Exception as e:
            logger.error(f"Apply template error: {e}")
            return jsonify({"error": str(e)}), 500

    # ==========================================
    # ERROR HANDLERS
    # ==========================================

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(429)
    def rate_limited(e):
        return (
            jsonify(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please slow down.",
                    "code": "RATE_LIMITED",
                }
            ),
            429,
        )

    return app


def init_db(db_path: str):
    """Initialize database with schema and seed data."""
    from core.db import connect_db

    conn = connect_db(db_path)
    cursor = conn.cursor()

    schema_path = Path(__file__).parent / "core" / "schema.sql"
    if schema_path.exists():
        with open(schema_path, "r") as f:
            cursor.executescript(f.read())
            conn.commit()

    # Run migrations for existing databases
    _run_migrations(conn)

    # Release stale lab claims
    try:
        from core.studios import StudioManager

        studio_mgr = StudioManager(db_path)
        studio_mgr.release_stale_claims()
    except Exception as e:
        logger.debug(f"Lab claim cleanup skipped: {e}")

    # Seed database with glazes and combinations
    seed_database(conn)
    if db_path == ":memory:":
        # Keep connection alive so the in-memory database persists
        _memory_db_connections["main"] = conn
    else:
        conn.close()


def _run_migrations(conn):
    """Run database migrations for existing databases."""
    cursor = conn.cursor()

    # Check if combinations table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='combinations'"
    )
    if not cursor.fetchone():
        return

    # Migration 1: Rename type values
    try:
        cursor.execute(
            "UPDATE combinations SET type = 'research-backed' WHERE type = 'proven'"
        )
        cursor.execute(
            "UPDATE combinations SET type = 'user-prediction' WHERE type = 'hypothesis'"
        )
    except sqlite3.OperationalError:
        pass

    # Migration 2: Add stage column if missing
    cursor.execute("PRAGMA table_info(combinations)")
    columns = [row[1] for row in cursor.fetchall()]
    if "stage" not in columns:
        cursor.execute("ALTER TABLE combinations ADD COLUMN stage TEXT DEFAULT 'idea'")
        # Backfill: research-backed → documented, user-prediction → idea
        cursor.execute(
            "UPDATE combinations SET stage = 'documented' WHERE type = 'research-backed' AND stage = 'idea'"
        )

    # Migration 3: Add prediction_grade column if missing
    if "prediction_grade" not in columns:
        cursor.execute(
            "ALTER TABLE combinations ADD COLUMN prediction_grade TEXT DEFAULT 'unknown'"
        )

    # Migration 4: Add firing log columns to experiments
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='experiments'"
    )
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(experiments)")
        exp_columns = [row[1] for row in cursor.fetchall()]
        firing_cols = {
            "clay_body": "TEXT",
            "firing_type": "TEXT",
            "cone": "TEXT",
            "application_method": "TEXT",
            "thickness": "TEXT",
            "drying_time": "TEXT",
            "cooling_notes": "TEXT",
            "atmosphere_notes": "TEXT",
            "confirmation": "TEXT",
            "fired_by": "TEXT",
            "fired_at": "TIMESTAMP",
            "studio_id": "TEXT",
        }
        for col_name, col_type in firing_cols.items():
            if col_name not in exp_columns:
                cursor.execute(
                    f"ALTER TABLE experiments ADD COLUMN {col_name} {col_type}"
                )

    conn.commit()
    logger.info("Database migrations completed")


def _load_seed_rules():
    """Load chemistry rules from ceramics-foundation/data/seed-chemistry-rules.json."""
    seed_path = Path(__file__).parent / "ceramics-foundation" / "data" / "seed-chemistry-rules.json"
    if not seed_path.exists():
        logger.warning(f"Seed rules not found: {seed_path}")
        return []
    try:
        with open(seed_path) as f:
            data = json.load(f)
        rules = data.get("rules", [])
        return [
            (
                r.get("category", ""),
                r.get("subcategory", ""),
                r.get("name", ""),
                r.get("description", ""),
                r.get("conditions", ""),
                r.get("outcome", ""),
                r.get("caveat", ""),
                r.get("confidence", "medium"),
            )
            for r in rules
        ]
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load seed rules: {e}")
        return []


def seed_database(conn):
    """Seed database with community glazes and combinations if empty."""
    cursor = conn.cursor()

    # Only seed if glazes table is empty
    cursor.execute("SELECT COUNT(*) FROM glazes")
    if cursor.fetchone()[0] > 0:
        return

    logger.info("Seeding database with community glazes and combinations...")

    # Load YAML template
    from core.templates import get_community_glazes

    template = get_community_glazes()
    if not template:
        logger.warning("No template found — skipping seed")
        return

    # Insert glazes from YAML
    for glaze in template.get("glazes", []):
        cursor.execute(
            """INSERT OR IGNORE INTO glazes
            (id, name, family, hex, chemistry, behavior, layering, warning, recipe, catalog_code, food_safe, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                glaze.get("id"),
                glaze.get("name"),
                glaze.get("family"),
                glaze.get("hex"),
                glaze.get("chemistry"),
                glaze.get("behavior"),
                glaze.get("layering"),
                glaze.get("warning"),
                glaze.get("recipe"),
                glaze.get("catalog_code"),
                glaze.get("food_safe"),
                glaze.get("notes"),
            ),
        )

    # Insert research-backed combinations
    for c in template.get("research_backed_combinations", []):
        layers_json = json.dumps([c.get("base"), c.get("top")])
        cursor.execute(
            """INSERT INTO combinations (base, top, layers, type, source, result, chemistry, risk, stage, prediction_grade)
            VALUES (?, ?, ?, 'research-backed', ?, ?, ?, ?, 'documented', ?)""",
            (
                c.get("base"),
                c.get("top"),
                layers_json,
                c.get("source"),
                c.get("result"),
                c.get("chemistry"),
                c.get("risk"),
                c.get("prediction_grade", "unknown"),
            ),
        )

    # Insert user-prediction combinations
    for c in template.get("user_prediction_combinations", []):
        layers_json = json.dumps([c.get("base"), c.get("top")])
        cursor.execute(
            """INSERT INTO combinations (base, top, layers, type, source, result, chemistry, risk, stage, prediction_grade)
            VALUES (?, ?, ?, 'user-prediction', ?, ?, ?, ?, 'idea', ?)""",
            (
                c.get("base"),
                c.get("top"),
                layers_json,
                c.get("source"),
                c.get("result"),
                c.get("chemistry"),
                c.get("risk"),
                c.get("prediction_grade", "unknown"),
            ),
        )

    # Load chemistry rules from JSON
    chemistry_rules = _load_seed_rules()

    # Merge with external chemistry-rules.json if available (external data takes precedence)
    try:
        from core.chemistry.data_loader import load_chemistry_rules

        external_rules = load_chemistry_rules()
        if external_rules:
            external_tuples = [
                (
                    r.get("category", ""),
                    r.get("subcategory", ""),
                    r.get("name", ""),
                    r.get("description", ""),
                    r.get("conditions", ""),
                    r.get("outcome", ""),
                    r.get("caveat", ""),
                    r.get("confidence", "medium"),
                )
                for r in external_rules
            ]
            external_keys = {(r[0], r[1], r[2]) for r in external_tuples}
            chemistry_rules = external_tuples + [
                r for r in chemistry_rules if (r[0], r[1], r[2]) not in external_keys
            ]
            logger.info(
                f"Loaded {len(external_tuples)} external rules, {len(chemistry_rules) - len(external_tuples)} from seed"
            )
    except ImportError:
        logger.debug("External data_loader not available, using seed rules only")

    for rule in chemistry_rules:
        cursor.execute(
            """INSERT INTO chemistry_rules
            (category, rule_type, title, description, conditions, outcomes, caveats, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            rule,
        )

    conn.commit()
    logger.info("Database seeded successfully")


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Get database connection."""
    from core.db import connect_db

    conn = connect_db(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# COMPATIBILITY CHECKER HELPERS
# ==========================================


def compute_compatibility(
    glaze_a_name: str, glaze_b_name: str, db_path: str = None
) -> dict:
    """Compute compatibility score between two glazes by name.

    Strategy: DB lookup → property-based scoring → string heuristic fallback.
    """
    # Try DB lookup first
    if db_path:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM glazes WHERE name = ? LIMIT 1", (glaze_a_name,))
        row_a = cursor.fetchone()
        cursor.execute("SELECT * FROM glazes WHERE name = ? LIMIT 1", (glaze_b_name,))
        row_b = cursor.fetchone()
        conn.close()

        if row_a and row_b:
            return compute_compatibility_from_properties(
                dict(row_a), dict(row_b), glaze_a_name, glaze_b_name
            )

    # String heuristic fallback
    return _compute_compatibility_string_matching(glaze_a_name, glaze_b_name)


def compute_compatibility_from_properties(
    glaze_a: dict, glaze_b: dict, name_a: str, name_b: str
) -> dict:
    """Score compatibility based on glaze properties."""
    score = 70  # Base score
    factors = []

    # Check layering hints
    layering_a = glaze_a.get("layering", "") or ""
    layering_b = glaze_b.get("layering", "") or ""
    if layering_a and layering_b:
        score += 5
        factors.append("Both glazes have layering information")

    # Check for Shino warning
    family_a = (glaze_a.get("family", "") or "").lower()
    family_b = (glaze_b.get("family", "") or "").lower()
    name_lower_a = name_a.lower()
    name_lower_b = name_b.lower()

    is_shino_a = "shino" in family_a or "shino" in name_lower_a
    is_shino_b = "shino" in family_b or "shino" in name_lower_b

    if is_shino_a != is_shino_b:
        score -= 15
        factors.append(
            "Shino over non-Shino: moderate crawling risk (thin application recommended)"
        )
    elif is_shino_a and is_shino_b:
        score += 5
        factors.append("Both glazes are Shino — similar chemistry expected")

    # Check for iron overload
    chemistry_a = (glaze_a.get("chemistry", "") or "").lower()
    chemistry_b = (glaze_b.get("chemistry", "") or "").lower()
    if "iron" in chemistry_a and "iron" in chemistry_b:
        score -= 10
        factors.append("Both glazes are iron-rich — may produce very dark results")

    # Check food safety compatibility
    food_safe_a = glaze_a.get("food_safe", "")
    food_safe_b = glaze_b.get("food_safe", "")
    if food_safe_a and food_safe_b:
        if food_safe_a.lower() in ("yes", "true") and food_safe_b.lower() in (
            "yes",
            "true",
        ):
            factors.append("Both glazes are food-safe")

    # Check warnings
    warning_a = glaze_a.get("warning", "") or ""
    warning_b = glaze_b.get("warning", "") or ""
    if warning_a:
        factors.append(f"Warning ({name_a}): {warning_a}")
    if warning_b:
        factors.append(f"Warning ({name_b}): {warning_b}")

    score = max(0, min(100, score))

    if score >= 80:
        verdict = "Excellent match"
    elif score >= 60:
        verdict = "Good compatibility"
    elif score >= 40:
        verdict = "Use with caution"
    else:
        verdict = "High risk — test first"

    return {
        "glaze_a": name_a,
        "glaze_b": name_b,
        "score": score,
        "verdict": verdict,
        "factors": factors,
        "method": "property-based",
    }


def _compute_compatibility_string_matching(glaze_a: str, glaze_b: str) -> dict:
    """Heuristic fallback when DB glazes are not found."""
    score = 65  # Neutral baseline
    factors = ["No database records found — using heuristic matching"]

    name_a = glaze_a.lower()
    name_b = glaze_b.lower()

    # Shino check
    is_shino_a = "shino" in name_a
    is_shino_b = "shino" in name_b
    if is_shino_a != is_shino_b:
        score -= 15
        factors.append("Shino over non-Shino: moderate crawling risk")
    elif is_shino_a and is_shino_b:
        score += 5

    # Clear glaze bonus
    if "clear" in name_a or "clear" in name_b:
        score += 10
        factors.append("Clear glaze — generally compatible with most bases")

    # Iron overload heuristic
    if "iron" in name_a and "iron" in name_b:
        score -= 10
        factors.append("Both appear iron-rich — may produce very dark results")

    score = max(0, min(100, score))

    if score >= 80:
        verdict = "Excellent match"
    elif score >= 60:
        verdict = "Good compatibility"
    elif score >= 40:
        verdict = "Use with caution"
    else:
        verdict = "High risk — test first"

    return {
        "glaze_a": glaze_a,
        "glaze_b": glaze_b,
        "score": score,
        "verdict": verdict,
        "factors": factors,
        "method": "string-heuristic",
    }


# Lazy app creation for WSGI — avoids import-time side effects (critical for tests)
class _AppProxy:
    def __init__(self):
        self._app = None

    def _ensure_app(self):
        if self._app is None:
            try:
                config = load_config()
                self._app = create_app(config)
            except ConfigurationError as e:
                logger.error(f"Failed to create app: {e}")
                raise
        return self._app

    def __call__(self, environ, start_response):
        return self._ensure_app()(environ, start_response)

    def __getattr__(self, name):
        return getattr(self._ensure_app(), name)


app = _AppProxy()

# Convenience for direct execution / development
if __name__ == "__main__":
    config = load_config()
    mode = config.get("mode")

    debug = config.get("server", {}).get("debug", False)
    if os.environ.get("FLASK_DEBUG", "").lower() not in ("true", "1"):
        debug = False

    host = config.get("server", {}).get("host", getattr(mode, "HOST", "127.0.0.1"))
    port = int(config.get("server", {}).get("port", getattr(mode, "PORT", 8767)))

    flask_app = create_app(config)

    print("=" * 50)
    print("OpenGlaze - Unified Glaze Management")
    print(f"Mode: {mode.name if hasattr(mode, 'name') else 'personal'}")
    print(f"Running on http://{host}:{port}")
    print(f"Debug: {debug}")
    print("=" * 50)

    flask_app.run(host=host, port=port, debug=debug)
