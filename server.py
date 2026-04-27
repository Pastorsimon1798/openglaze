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
    configured_port = os.environ.get("FLASK_PORT", "8768")
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
        except Exception:
            pass
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
                "version": "1.0.0",
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
        return send_from_directory("frontend", path)

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
                yield f"data: {json.dumps({'type': 'error', 'ai_available': False, 'content': 'AI backend unavailable. Please ensure Ollama is running or configure ANTHROPIC_API_KEY.'})}\n\n"
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
                        "help": "For Ollama: run 'ollama serve' or check your OLLAMA_API endpoint. For cloud: set ANTHROPIC_API_KEY environment variable.",
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
            resp = jsonify({"error": "Both glaze_a and glaze_b are required"})
            resp.status_code = 400
            return resp

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
            resp = jsonify({"error": str(e)})
            resp.status_code = 500
            return resp

    # ==========================================
    # PREDICTIONS API ROUTES (auth required)
    # ==========================================

    @app.route("/api/predictions", methods=["POST"])
    @rate_limit(requests_per_minute=30)
    def create_prediction():
        """Create a prediction for a combination."""
        if not PREDICTIONS_AVAILABLE:
            resp = jsonify({"error": "Predictions not available"})
            resp.status_code = 503
            return resp

        user_id = get_current_user_id()
        if not user_id:
            resp = jsonify({"error": "Authentication required"})
            resp.status_code = 401
            return resp

        data = request.json or {}
        combo_id = data.get("combo_id")
        predicted_outcome = data.get("predicted_outcome", "")
        confidence = data.get("confidence", 50)

        if not combo_id or not predicted_outcome:
            resp = jsonify({"error": "combo_id and predicted_outcome are required"})
            resp.status_code = 400
            return resp

        try:
            result = g.prediction_manager.create_prediction(
                user_id, combo_id, predicted_outcome, confidence
            )
            resp = jsonify(result)
            resp.status_code = 201
            return resp
        except Exception as e:
            logger.error(f"Create prediction error: {e}")
            resp = jsonify({"error": str(e)})
            resp.status_code = 500
            return resp

    @app.route("/api/predictions/leaderboard")
    @rate_limit(requests_per_minute=60)
    def get_prediction_leaderboard():
        """Get prediction leaderboard (user vs AI)."""
        if not PREDICTIONS_AVAILABLE:
            resp = jsonify({"error": "Predictions not available"})
            resp.status_code = 503
            return resp

        user_id = get_current_user_id()
        if not user_id:
            resp = jsonify({"error": "Authentication required"})
            resp.status_code = 401
            return resp

        try:
            leaderboard = g.prediction_manager.get_leaderboard(user_id)
            return jsonify(leaderboard)
        except Exception as e:
            logger.error(f"Leaderboard error: {e}")
            resp = jsonify({"error": str(e)})
            resp.status_code = 500
            return resp

    # ==========================================
    # GAMIFICATION API ROUTES (auth required)
    # ==========================================

    @app.route("/api/stats")
    @rate_limit(requests_per_minute=60)
    def get_user_stats():
        """Get user gamification stats and badges."""
        if not GAMIFICATION_AVAILABLE:
            resp = jsonify({"error": "Gamification not available"})
            resp.status_code = 503
            return resp

        user_id = get_current_user_id()
        if not user_id:
            resp = jsonify({"error": "Authentication required"})
            resp.status_code = 401
            return resp

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
            resp = jsonify({"error": str(e)})
            resp.status_code = 500
            return resp

    @app.route("/api/progress")
    @rate_limit(requests_per_minute=60)
    def get_progress():
        """Get user progress — combo counts + gamification stats."""
        if not GAMIFICATION_AVAILABLE:
            resp = jsonify({"error": "Gamification not available"})
            resp.status_code = 503
            return resp

        user_id = get_current_user_id()
        if not user_id:
            resp = jsonify({"error": "Authentication required"})
            resp.status_code = 401
            return resp

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
            resp = jsonify({"error": str(e)})
            resp.status_code = 500
            return resp

    # ==========================================
    # TEMPLATES API ROUTES (mixed auth)
    # ==========================================

    @app.route("/api/templates")
    def get_templates():
        """List available templates."""
        if not TEMPLATES_AVAILABLE:
            resp = jsonify({"error": "Templates not available"})
            resp.status_code = 503
            return resp
        try:
            templates = list_templates()
            return jsonify(templates)
        except Exception as e:
            logger.error(f"List templates error: {e}")
            resp = jsonify({"error": str(e)})
            resp.status_code = 500
            return resp

    @app.route("/api/templates/<template_id>")
    def get_template(template_id):
        """Get a specific template by ID."""
        if not TEMPLATES_AVAILABLE:
            resp = jsonify({"error": "Templates not available"})
            resp.status_code = 503
            return resp
        try:
            template = load_template(template_id)
            if template:
                return jsonify(template)
            resp = jsonify({"error": "Template not found"})
            resp.status_code = 404
            return resp
        except Exception as e:
            logger.error(f"Load template error: {e}")
            resp = jsonify({"error": str(e)})
            resp.status_code = 500
            return resp

    @app.route("/api/templates/<template_id>/apply", methods=["POST"])
    @rate_limit(requests_per_minute=10)
    def apply_template(template_id):
        """Apply a template — insert glazes into user's account."""
        if not TEMPLATES_AVAILABLE:
            resp = jsonify({"error": "Templates not available"})
            resp.status_code = 503
            return resp

        user_id = get_current_user_id()
        if not user_id:
            resp = jsonify({"error": "Authentication required"})
            resp.status_code = 401
            return resp

        try:
            template = load_template(template_id)
            if not template:
                resp = jsonify({"error": "Template not found"})
                resp.status_code = 404
                return resp

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
            resp = jsonify({"error": str(e)})
            resp.status_code = 500
            return resp

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

    # Insert chemistry rules
    chemistry_rules = [
        # Color prediction (8)
        (
            "color_prediction",
            "oxide_atmosphere",
            "Iron 2% + oxidation = amber/tan",
            "Iron oxide at ~2% in an oxidation (oxygen-rich) atmosphere produces warm amber to tan colors.",
            "Iron oxide 2%, oxidation atmosphere",
            "Amber, tan, or light brown",
            "Color varies with base glaze chemistry and iron source (red iron oxide vs black iron oxide). Calcium-heavy bases shift toward yellow-tan; potassium-heavy bases allow warmer reds.",
            "high",
        ),
        (
            "color_prediction",
            "oxide_atmosphere",
            "Iron 2% + reduction = celadon green",
            "Iron oxide at ~2% in a reduction (oxygen-depleted) atmosphere produces the classic celadon green.",
            "Iron oxide 2%, reduction atmosphere",
            "Celadon green to blue-green",
            "Depth of green depends on reduction intensity. Light reduction = gray-green; heavy reduction = deeper green. Calcium promotes celadon color; high boron can wash it out.",
            "high",
        ),
        (
            "color_prediction",
            "oxide_atmosphere",
            "Copper 1% + oxidation = green",
            "Copper oxide at ~1% in oxidation produces reliable greens ranging from mint to forest green.",
            "Copper oxide 1%, oxidation atmosphere",
            "Green (mint to forest)",
            "Higher copper percentages deepen the green. Above ~3% may produce very dark green approaching black. Calcium fluxes produce turquoise-greens; sodium fluxes shift toward blue-green.",
            "high",
        ),
        (
            "color_prediction",
            "oxide_atmosphere",
            "Copper 1% + heavy reduction = copper red",
            "Copper oxide at ~1% in heavy reduction CAN produce copper red (sang de boeuf), but this is one of the most difficult and unpredictable effects in ceramics.",
            "Copper oxide 1%, heavy reduction atmosphere, controlled cooling, thick application",
            "Copper red to oxblood red — when it works",
            "~50-60% failure rate for beginners, improving to 20-40% with experience. Requires: precise reduction timing (not too early or copper re-oxidizes), slow controlled cooling through 1500°F-1800°F, thick application (thin coats go green), specific base chemistry (low alumina, adequate silica). Many potters fire dozens of pieces before achieving consistent results. Consider this advanced.",
            "medium",
        ),
        (
            "color_prediction",
            "oxide_stable",
            "Cobalt 0.5-2% = blue in any atmosphere",
            "Cobalt oxide is among the most reliable ceramic colorants. Small amounts produce strong blues in most atmospheres, though magnesium can shift toward lavender and iron toward blue-green.",
            "Cobalt oxide 0.5-2%, any atmosphere",
            "Blue — from pale sky blue (0.5%) to deep cobalt blue (2%)",
            "Cobalt is very strong. Above 2% it tends toward black. Combined with iron it produces blue-greens. With magnesium it can produce lavender.",
            "high",
        ),
        (
            "color_prediction",
            "oxide_atmosphere",
            "Manganese 2-8% + oxidation = purple/brown",
            "Manganese dioxide at 2-8% in oxidation produces purples and browns. Lower percentages give purple, higher give brown.",
            "Manganese dioxide 2-8%, oxidation atmosphere",
            "Purple (low %) to warm brown (high %)",
            "Manganese can become volatile at cone 6+ temperatures, potentially affecting nearby pieces. Use ventilation.",
            "high",
        ),
        (
            "color_prediction",
            "oxide_atmosphere",
            "Manganese + reduction = metallic brown/black",
            "Manganese in reduction produces metallic browns and blacks. The reduction atmosphere changes the color significantly compared to oxidation.",
            "Manganese dioxide, reduction atmosphere",
            "Metallic brown to black",
            "WARNING: Manganese fumes are toxic during firing. Always fire with adequate ventilation. Some studios avoid manganese entirely for health reasons.",
            "high",
        ),
        (
            "color_prediction",
            "oxide_interaction",
            "Chrome + tin = pink",
            "Chromium oxide combined with tin oxide produces pink. This is a classic ceramic color interaction.",
            "Chromium oxide + tin oxide in base glaze",
            "Pink to mauve",
            "Very sensitive to proportions. Too much chrome = green; too much tin = white. The sweet spot is narrow. Chrome can also cause glaze defects (crawling, pinholing) in some bases. CRITICAL: Zinc in the base glaze will turn chrome-tin pinks brown. Use zinc-free bases for reliable pinks. Best results in oxidation. In reduction, chrome may reduce to darker compounds, muting the pink.",
            "medium",
        ),
        # Layering principles (6)
        (
            "layering_principle",
            "compatibility",
            "Similar chemistry = compatible",
            "Glazes with similar base chemistry (same flux family, similar thermal expansion) tend to be compatible when layered.",
            "Two glazes with similar silica/alumina/flux ratios",
            "Low risk of defects (crawling, crazing, shivering)",
            "Similar chemistry is a guideline, not a guarantee. Application thickness and drying time between layers also matter.",
            "high",
        ),
        (
            "layering_principle",
            "compatibility",
            "High iron over high iron = too dark",
            "When both the base and top glaze are iron-rich, the combined iron can produce mud-brown or near-black results, losing the character of both glazes.",
            "Two glazes both with >2% iron oxide",
            "Very dark brown to black, loss of individual character",
            "Some potters intentionally create dark moody surfaces this way. If that's the goal, lean into it.",
            "high",
        ),
        (
            "layering_principle",
            "atmosphere_sensitivity",
            "Copper glazes are sensitive to reduction",
            "Copper-containing glazes change color based on atmosphere. In oxidation they're green; in reduction they can go red, metallic, or become nearly colorless depending on reduction intensity.",
            "Any glaze containing copper, variable atmosphere",
            "Green in oxidation, red/metallic/clear in reduction",
            "Copper sensitivity means uneven reduction in the kiln can cause mottled, unexpected results. This can be beautiful or frustrating depending on your goal.",
            "high",
        ),
        (
            "layering_principle",
            "layering_effect",
            "Clear glazes add depth without changing color",
            "A clear glaze over another glaze adds gloss and depth, making the underlying color appear richer. Most clears shift color slightly — use a truly neutral clear (not blue- or yellow-tinted) to minimize color shift.",
            "Clear transparent glaze over colored glaze",
            "Deeper, glossier version of base color",
            "The clear must be truly transparent. Some 'clears' have a slight blue or yellow cast that will shift the base color.",
            "high",
        ),
        (
            "layering_principle",
            "layering_effect",
            "White opaque glazes can cover dark bases",
            "A white opaque (or semi-opaque) glaze over a dark glaze can lighten or hide the dark base, creating pastel or broken-color effects.",
            "White opaque glaze over dark glaze",
            "Lightened base color to full white coverage depending on thickness",
            "Very thick application can fully cover the base. Thin application creates interesting break-and-flow patterns where the dark base shows through.",
            "high",
        ),
        (
            "layering_principle",
            "compatibility",
            "Shino over non-Shino = high risk crawling",
            "Shino glazes have high feldspar content and can crawl when applied over glazes with different chemistry. Risk level: MODERATE to HIGH depending on base glaze chemistry and application. Thin application reduces risk. Some potters intentionally chase crawl textures for aesthetic effect.",
            "Shino glaze over non-Shino base",
            "MODERATE to HIGH risk of crawling (glaze pulls away from surface in patches)",
            "Some combinations do work, especially if the base glaze is also high in feldspar. Some potters intentionally chase crawl textures for aesthetic effect. If you want to try it: apply Shino thin, apply over a similar high-feldspar base, and accept that results will vary. NOT guaranteed to crawl.",
            "high",
        ),
        # Common issues (5)
        (
            "common_issue",
            "defect",
            "Crawling",
            "Crawling occurs when glaze pulls away from the clay body during firing, leaving bare patches. It's caused by poor adhesion between glaze and body, or incompatibility between layered glazes.",
            "Dust on bisque, greasy surface, incompatible layered glazes, glaze applied too thick, Shino over non-Shino",
            "Bare patches where glaze has receded, sometimes with sharp edges",
            "Light crawling can be intentional and beautiful. Prevent by: cleaning bisque with damp sponge, letting each layer dry fully before applying next, keeping first layer thin.",
            "high",
        ),
        (
            "common_issue",
            "defect",
            "Running",
            "Running occurs when glaze becomes too fluid during firing and flows off the piece, often pooling at the base.",
            "Glaze applied too thick, over-fired, glaze with low melting point, certain combinations with different melt temperatures",
            "Glaze flows off surfaces, pools at base, can stick to kiln shelf",
            "Prevent by: applying thinner coats, using kiln wash on shelves, placing a catch plate under suspect pieces. Some running can create beautiful flowing effects.",
            "high",
        ),
        (
            "common_issue",
            "defect",
            "Pinholing",
            "Pinholing appears as small pits or holes in the glaze surface, caused by gas bubbles escaping during firing that don't heal over.",
            "Trapped air in clay body, organic material in clay, glaze applied too thin, fast firing, underfiring (glaze hasn't fully melted to heal)",
            "Small pits or holes in glaze surface, can feel rough to the touch",
            "Prevent by: bisque firing to cone 06-04 (not 08), slowing the firing, slightly thicker glaze application, holding at peak temperature briefly to allow glaze to level.",
            "high",
        ),
        (
            "common_issue",
            "defect",
            "Crazing",
            "Crazing is a network of fine cracks in the glaze surface, caused by mismatch in thermal expansion between glaze and clay body. The glaze contracts more than the body as it cools.",
            "Glaze thermal expansion > clay body thermal expansion, fast cooling, thin-walled pieces",
            "Fine spider-web crack pattern in glaze surface, can appear immediately or over time",
            "Crazing is primarily a functional issue for food-safe ware (bacteria can get into cracks). It's sometimes intentional for aesthetic effect (crackle glazes). Prevent by: adjusting glaze silica/alumina ratio, slower cooling, using a glaze with thermal expansion closer to your clay body.",
            "high",
        ),
        (
            "common_issue",
            "defect",
            "Thermal shock / dunting",
            "Dunting is cracking that occurs during cooling, caused by thermal stress. Pieces crack or shatter, often with a sharp ping sound.",
            "Fast cooling, thick pieces, uneven wall thickness, silica conversion zone (1063°F/573°C) cooled too fast",
            "Cracks or shattering during cooling, often sudden with audible ping",
            "Prevent by: slow cooling through 1000°F-1100°F (hold for 30-60 minutes), avoiding thick sections, uniform wall thickness. Dunting is irreversible — the piece is lost.",
            "high",
        ),
        # Atmosphere effects (2)
        (
            "atmosphere_effect",
            "oxidation",
            "Oxidation atmosphere effects",
            "Oxidation (oxygen-rich) firing produces predictable, stable colors. Iron goes warm, copper goes green, most colorants behave consistently.",
            "Oxidation atmosphere (air damper open, plenty of oxygen)",
            "Iron: amber/tan/yellow. Copper: green. Cobalt: blue. Manganese: purple/brown.",
            "Oxidation is generally more predictable and forgiving than reduction. Good for functional ware where consistency matters.",
            "high",
        ),
        (
            "atmosphere_effect",
            "reduction",
            "Reduction atmosphere effects",
            "Reduction (oxygen-depleted) firing creates richer, more varied colors by stripping oxygen from oxides. Iron goes green, copper can go red, surfaces can become more complex.",
            "Reduction atmosphere (damper partially closed, fuel-rich)",
            "Iron: celadon green to gray. Copper: can go red/metallic/clear. Surfaces: more varied, often more complex.",
            "Reduction is less predictable. Uneven reduction causes uneven results. Copper reds especially are unreliable (~50-60% failure rate for beginners, improving with experience). Results vary by position in kiln.",
            "high",
        ),
        # Application effects (2)
        (
            "application_effect",
            "thickness",
            "Thin application effects",
            "Thinly applied glaze produces lighter, more subtle colors and shows more of the clay body texture. Also lower risk of running, crawling, and other defects.",
            "Glaze applied in 1-2 thin coats",
            "Lighter color, more texture showing through, lower defect risk",
            "Too thin and the glaze may be rough or partially uncovered. Some glazes (especially crawling-prone ones like Shino) benefit from thin application.",
            "high",
        ),
        (
            "application_effect",
            "thickness",
            "Thick application effects",
            "Thickly applied glaze produces deeper, richer colors and more pooling variation. Higher risk of running, crawling, and pinholing.",
            "Glaze applied in 3+ coats or very thick single coat",
            "Deeper/richer color, more pooling and variation, higher running and crawling risk",
            "Thick application is critical for copper reds to develop (thin coats go green). Some glazes are designed for thick application. Be aware of kiln shelf protection — use wadding or catch plates.",
            "high",
        ),
        # Firing effects (2)
        (
            "firing_effect",
            "speed",
            "Fast firing effects",
            "Fast firing (quick temperature rise) produces more varied and textured surfaces but increases defect risk.",
            "Firing rate: fast (several hours to cone 10)",
            "More texture and variation, higher defect risk (pinholing, bloating, cracking)",
            "Fast firing can work well for sculptural or textured pieces where variation is desirable. Not recommended for functional ware where consistency matters.",
            "medium",
        ),
        (
            "firing_effect",
            "cooling",
            "Slow cooling effects",
            "Slow controlled cooling produces smoother, more consistent surfaces and better color development, especially for glazes sensitive to thermal shock.",
            "Controlled slow cooling, optional hold at 1000-1500°F",
            "Smoother surface, better crystal growth, more consistent color, reduced cracking risk",
            "Slow cooling through 1500-1800°F significantly improves copper red development and consistency. A 30-60 minute hold in this range is recommended.",
            "high",
        ),
        # NEW RULES ADDED HERE
        (
            "layering_principle",
            "material_interaction",
            "Zinc affects multiple colorants",
            "Zinc oxide in a base glaze interacts with several colorants, sometimes in unwanted ways. Understanding zinc interactions is important when choosing glazes to layer.",
            "Zinc oxide present in base glaze",
            "Chrome-tin pinks turn brown; copper color development can shift; iron greens may become lighter or browner",
            "Always check base glaze for zinc before applying chrome-tin pink glazes. Some popular clear glazes contain zinc and will ruin pinks.",
            "high",
        ),
        (
            "application_effect",
            "material_property",
            "Boron as a powerful flux",
            "Boron (from borax, gerstley borate, or frits) is a very powerful flux that lowers melting temperature significantly. It affects color development and can cause running at high temperatures.",
            "Boron-containing materials in glaze",
            "Lower melting temperature, potential color shifts, increased running risk",
            "Boron can turn some blue glazes green and affect chrome-based colors. High boron glazes may run more than expected. Common in many commercial low-fire and mid-range glazes.",
            "high",
        ),
        # Material safety (12)
        (
            "material_safety",
            "dust_hazard",
            "Silica dust — respirable crystalline silica",
            "Silica dust (from silica, flint, quartz) is the most serious long-term health hazard in ceramics. Prolonged inhalation causes silicosis, an irreversible and progressive lung disease. Silica is found in almost all glazes and many clay bodies.",
            "Mixing dry glaze materials, sanding fired pieces, cleaning up dry spills",
            "Silicosis risk with chronic exposure; irritation of eyes, nose, throat with acute exposure",
            "Wet methods for cleanup (never dry sweep). Wear N95 minimum when mixing, P100 when sanding. Silicosis develops over years of exposure — protect yourself every time, even for small jobs.",
            "high",
        ),
        (
            "material_safety",
            "fume_hazard",
            "Manganese fumes — toxic above 1900°F",
            "Manganese dioxide becomes volatile above ~1900°F (1040°C) during firing, releasing toxic fumes. Inhalation can cause manganese poisoning (manganism) with neurological symptoms similar to Parkinson's disease.",
            "Firing glazes containing manganese dioxide, especially above 1900°F",
            "Manganism with chronic exposure: tremors, muscle rigidity, mood changes; acute irritation of respiratory tract",
            "Always fire manganese-containing glazes with adequate kiln ventilation. Some studios avoid manganese entirely. Never fire manganese glazes in an enclosed or poorly ventilated space. Risk increases with manganese percentage.",
            "high",
        ),
        (
            "material_safety",
            "toxicity",
            "Barium toxicity",
            "Barium carbonate is used as a flux in some glazes. Soluble barium compounds are poisonous if ingested. Barium carbonate itself is relatively insoluble, making it safer than soluble barium salts, but it can become soluble under acidic conditions (like stomach acid or acidic food).",
            "Glazes containing barium carbonate, especially functional ware",
            "Soluble barium is toxic if ingested — affects heart, muscles, nerves; can cause cardiac arrest in severe cases",
            "Barium carbonate is commonly used in matte glazes. The risk is primarily for food-contact surfaces where acidic food (citrus, vinegar, coffee) could leach barium. Avoid barium in functional ware glazes or ensure the glaze is fully mature and acid-resistant.",
            "high",
        ),
        (
            "material_safety",
            "extreme_toxicity",
            "Lead — extremely toxic, never for functional ware",
            "Lead is EXTREMELY TOXIC and should never be used in functional pottery. Lead glazes were historically common but are now known to cause serious health problems including neurological damage, especially in children. Lead exposure can occur from leaching into food/beverages.",
            "Any glaze containing lead compounds (lead bisilicate, red lead, lead frits)",
            "Neurological damage, developmental delays in children, organ damage, death in severe cases",
            "Some legacy glaze recipes contain lead. Never use these for functional ware, even if fired to maturity. Some lead frits (fritted lead) are safer than raw lead but still carry risk. Many countries ban lead in food-contact ceramics entirely. There is no safe level of lead exposure for children.",
            "high",
        ),
        (
            "material_safety",
            "carcinogen",
            "Cadmium — carcinogen, avoid for functional ware",
            "Cadmium is a known carcinogen used to produce bright reds, oranges, and yellows in ceramics. Cadmium exposure is linked to lung cancer, kidney damage, and bone disease. Inhalation during mixing is the primary risk.",
            "Glazes containing cadmium compounds (cadmium red, cadmium yellow)",
            "Lung cancer risk with inhalation; kidney damage; bone disease (Itai-Itai disease with chronic exposure)",
            "Cadmium produces beautiful colors but should never be used in functional ware. Commercial cadmium glazes are often encapsulated in frits to reduce leaching risk, but this is not 100% effective. Always wear a respirator when mixing cadmium-containing materials. Consider alternative colorants (iron red, chrome-tin pink) for food-safe reds.",
            "high",
        ),
        (
            "material_safety",
            "valence_toxicity",
            "Chromium VI vs III — oxidation state matters",
            "Chromium exists in multiple oxidation states with very different toxicity profiles. Chromium(VI) is a known carcinogen, while chromium(III) is relatively safe and is actually an essential trace nutrient. Ceramic glazes typically contain chromium(III) as chromium oxide.",
            "Chromium oxide (Cr2O3) in glazes — this is Cr(III)",
            "Cr(VI): carcinogenic, causes lung cancer, skin ulcers; Cr(III) in glazes: generally safe, low toxicity",
            "Chromium(III) oxide in ceramic glazes is not considered a significant health risk. The concern is during firing — under certain conditions, Cr(III) could theoretically oxidize to Cr(VI), though this is rare in normal pottery firing. Good kiln ventilation reduces any risk. Cr(VI) is a workplace hazard in industrial settings, not typically a concern for studio potters using chromium oxide.",
            "high",
        ),
        (
            "material_safety",
            "sensitizer",
            "Nickel — skin sensitizer and inhalation hazard",
            "Nickel compounds are common skin sensitizers that can cause allergic contact dermatitis. Nickel is also an inhalation hazard during mixing of dry glaze materials and is classified as a possible carcinogen (IARC Group 2B).",
            "Mixing dry glazes containing nickel oxide or nickel compounds",
            "Allergic contact dermatitis (skin rash); respiratory irritation with inhalation; possible carcinogen with chronic exposure",
            "Nickel allergies develop through repeated skin contact. Once sensitized, even small exposures can trigger reactions. Wear gloves when handling nickel compounds and a respirator when mixing. Nickel is sometimes used to produce brown and gray colors.",
            "medium",
        ),
        (
            "material_safety",
            "toxicity",
            "Lithium — toxic if ingested, handle with gloves",
            "Lithium carbonate and lithium-containing materials (spodumene, petalite) are used as fluxes in glazes. Lithium is toxic if ingested and can cause lithium poisoning with symptoms affecting the nervous system, kidneys, and thyroid.",
            "Handling lithium carbonate or lithium-bearing feldspars",
            "Nausea, tremors, confusion with ingestion; skin irritation with prolonged contact",
            "Lithium is primarily an ingestion risk, not an inhalation risk. Wear gloves when handling lithium carbonate powder. Spodumene and petalite (lithium feldspars) contain lower concentrations and are less hazardous. Lithium is commonly used in shino glazes and as a high-temperature flux.",
            "medium",
        ),
        (
            "material_safety",
            "ppe",
            "Respirator requirements for pottery",
            "Respiratory protection is essential when handling dry ceramic materials. Different activities require different levels of protection based on the hazard.",
            "Any dry material handling: mixing glazes, sanding, cleaning dust",
            "N95 minimum for mixing dry glazes; P100 for sanding fired pieces; full facepiece with P100 cartridges for spraying glazes",
            "N95 filters particulates but not chemical fumes. P100 filters are more efficient. For spraying, you need both particulate and organic vapor protection. Fit testing ensures the respirator seals properly. Facial hair prevents a proper seal. Replace filters regularly — clogged filters make breathing harder and reduce protection.",
            "high",
        ),
        (
            "material_safety",
            "ventilation",
            "Kiln ventilation requirements",
            "Kilns produce gases (sulfur, carbon monoxide, potentially toxic metal fumes) during firing. Proper ventilation is essential for safety, both for the kiln operator and anyone in the building.",
            "Any kiln firing, especially reduction firing and glazes with toxic materials",
            "Minimum 100-150 fpm face velocity for hood capture; never fire in enclosed living space; cross-ventilation for gas kilns",
            "Never fire a kiln in a living space or attached garage without dedicated ventilation. Gas kilns produce carbon monoxide — a colorless, odorless, deadly gas. Electric kilns produce fewer fumes but still off-gas from glaze materials. Downdraft vent systems are most effective. Windows alone are not sufficient ventilation.",
            "high",
        ),
        (
            "material_safety",
            "cleanup",
            "Cleanup safety — wet methods only",
            "Dry ceramic dust is the primary route of hazardous exposure in pottery studios. All cleanup should use wet methods to prevent dust from becoming airborne.",
            "Cleaning studio surfaces, glaze spills, clay scraps",
            "Wet mop or damp sponge for floors; wet wipe for work surfaces; HEPA vacuum if dry cleaning is unavoidable",
            "NEVER dry sweep — this puts silica and other hazardous dust into the air where you breathe it. A damp mop or sponge is the safest cleanup method. If you must vacuum, use a HEPA-filtered vacuum — standard vacuums exhaust fine dust back into the air. Keep studio surfaces damp during extended work sessions.",
            "high",
        ),
        (
            "material_safety",
            "high_exposure",
            "Glaze dust during sanding — full PPE required",
            "Sanding fired glaze creates fine particulate dust containing silica, colorant metals, and potentially toxic compounds. This is one of the highest-exposure activities in pottery.",
            "Sanding fired glaze surfaces to smooth rough spots, remove kiln shelf residue",
            "High exposure to respirable crystalline silica and metal oxide dusts",
            "This activity requires the highest level of protection: P100 respirator minimum, safety glasses, ideally work in a ventilated area or use wet sanding. Wet sanding eliminates dust entirely and is strongly preferred. If dry sanding is necessary, consider doing it outdoors. Sanding created the dust hazard — never skip protection for a 'quick sand.'",
            "high",
        ),
        # Food safety (8)
        (
            "food_safety",
            "leaching",
            "Food safety definition — leaching and bacterial risk",
            "A food-safe glaze is one that does not leach toxic levels of metals into food or beverages, and has a smooth, non-porous surface that does not harbor bacteria. Two separate concerns: chemical safety (metal leaching) and physical safety (surface texture/bacteria).",
            "Any glazed vessel intended for food or beverage contact",
            "Safe glaze: fully mature, smooth surface, no toxic colorants leaching, passes acid test",
            "Food safety is not a simple yes/no. A glaze can be chemically safe (no toxic leaching) but physically unsafe (rough or crazed surface). Both conditions must be met for functional ware. Decorative pieces don't need food safety but should be labeled as non-food-safe.",
            "high",
        ),
        (
            "food_safety",
            "defect_risk",
            "Crazing = not food safe for functional ware",
            "Crazed glazes (network of fine cracks in the surface) are not considered food-safe for functional ware. The crack network can harbor bacteria that are difficult to remove through normal washing, creating a potential health hazard.",
            "Glaze with visible crackle pattern, used for food/beverage",
            "Bacteria growth in crack network; staining over time; potential food contamination",
            "Some potters argue that proper dishwashing kills bacteria in crazed glazes. While partially true, the crack network protects bacteria from detergent and hot water, making thorough cleaning impossible. Crazing that appears after repeated use (delayed crazing) is especially concerning because the user may not notice. Intentional crackle glazes should be clearly labeled decorative-only.",
            "high",
        ),
        (
            "food_safety",
            "toxic_colorants",
            "Toxic colorants to avoid for functional ware",
            "Some common ceramic colorants are toxic enough that they should be avoided entirely in functional ware, regardless of how well-fired the glaze is. The risk of leaching is too high.",
            "Functional ware glazes containing: lead (any amount), cadmium (any amount), high barium (>5%), high manganese (>5%)",
            "Potential metal leaching into food/beverage, especially under acidic conditions",
            "Iron, cobalt, and titanium are generally considered safe for food surfaces when properly fired. Copper is borderline — it can leach under acidic conditions. Chrome-tin combinations (for pinks) are generally safe at low percentages. When in doubt, use a liner glaze (food-safe clear) on the interior of functional pieces and decorative glazes only on the exterior.",
            "high",
        ),
        (
            "food_safety",
            "acid_leaching",
            "Acid resistance — citrus and vinegar leach metals",
            "Acidic foods and beverages (citrus, vinegar, coffee, wine, tomato sauce) can leach metals from improperly fired or unsuitable glazes at much higher rates than neutral foods. This is the primary vector for toxic exposure from glazed ceramics.",
            "Glazed vessel used for acidic food or drink (lemon juice, vinegar, coffee, wine, tomato)",
            "Increased leaching of barium, copper, manganese, cadmium, and other metals under acidic conditions",
            "Always test food-safe glazes with acidic foods. A glaze that passes a water leach test may fail with vinegar or lemon juice. The FDA uses a 4% acetic acid (vinegar) solution for leach testing. Home test: fill vessel with white vinegar for 24 hours — if the glaze changes color or the vinegar tastes metallic, it is not acid-resistant. Consider a food-safe liner for mugs and bowls.",
            "high",
        ),
        (
            "food_safety",
            "testing",
            "Food safety testing methods",
            "Testing is the only way to confirm a glaze is food-safe. There are two levels: home screening and professional laboratory testing.",
            "Any glaze intended for food/beverage use",
            "Home lead test kits: quick screening for lead only, limited accuracy; Lab ICP-MS testing: comprehensive metal analysis, 100-200 USD per sample",
            "Home lead test kits (available at hardware stores) are inexpensive but only test for lead and can give false negatives. They are a reasonable first screen. For comprehensive testing, send samples to a lab that does ICP-MS (inductively coupled plasma mass spectrometry) testing — this detects all metal leaching at very low levels. Some universities with ceramics programs offer testing. The cost is worth it for production ware or gifts.",
            "high",
        ),
        (
            "food_safety",
            "commercial_assumptions",
            "Commercial glaze food safety claims",
            "Commercial glaze manufacturers often label their glazes as 'food-safe' or 'dinnerware-safe.' While these claims are generally trustworthy, they depend on correct application and firing.",
            "Using commercially prepared glazes for functional ware",
            "Manufacturer claims are a good starting point but not a guarantee of safety",
            "Food-safe claims assume: correct application thickness, proper firing to the recommended cone, appropriate cooling rate, and use on the recommended clay body. If you underfire, overapply, or use an unusual clay body, the glaze may not be food-safe despite the manufacturer's claim. Always verify with testing if you deviate from manufacturer instructions. Layering commercial glazes can also compromise food safety.",
            "medium",
        ),
        (
            "food_safety",
            "maturity",
            "Glaze maturity and leaching",
            "Underfired glazes leach metals at much higher rates than fully mature glazes. A glaze that is food-safe at cone 10 may not be food-safe at cone 8. Ensuring full maturity is critical for food safety.",
            "Glaze fired below its intended temperature (underfired by even half a cone)",
            "Dramatically increased metal leaching from underfired glazes; surface may appear properly melted but not be fully reacted",
            "Visual inspection is not reliable — an underfired glaze can look fully melted but still leach metals. Use witness cones in every firing to verify temperature. If cones show the kiln underfired, treat all functional ware from that firing as not food-safe. This is especially important in gas kilns where temperature varies by location — pieces in cooler spots may be underfired even if pieces near the burner are mature.",
            "high",
        ),
        (
            "food_safety",
            "surface_texture",
            "Surface texture and bacterial harboring",
            "Rough, crawled, or pitted glaze surfaces can harbor bacteria just like crazed surfaces, making them unsuitable for food contact even if the glaze chemistry is safe.",
            "Glaze with rough texture, crawling, pinholing, or other surface defects on food-contact surface",
            "Bacteria can lodge in surface irregularities and resist normal washing",
            "This applies to intentional textures too — some potters create deliberately rough surfaces for aesthetic reasons. These are fine for decorative pieces but should not be used for food or beverage contact. If a functional piece develops crawling or pinholing, consider it not food-safe even if the glaze chemistry is otherwise safe. The interior of bowls, cups, and plates should always be smooth and fully covered.",
            "high",
        ),
        # Firing effects — cooling rate rules (8)
        (
            "firing_effect",
            "cooling",
            "Copper red critical cooling window",
            "Copper reds (sang de boeuf) require a specific cooling hold to develop. Without controlled cooling through 1500-1800°F, copper re-oxidizes and the piece goes green or clear. This is the single most important factor in copper red success.",
            "Copper red glaze at cone 10 reduction",
            "Hold at 1500-1800°F for 30-60 minutes, then controlled cooling; skipping this step almost always produces green",
            "The hold allows copper to remain in the reduced (Cu+) state while the glaze stiffens enough to lock in the color. Opening the kiln too early introduces oxygen and ruins the red. This is why copper reds have such high failure rates — the cooling is as important as the firing. Some potters crash cool to 1500°F, then hold, then natural cool.",
            "high",
        ),
        (
            "firing_effect",
            "cooling",
            "Crystal glaze slow cooling requirements",
            "Macro-crystalline glazes (visible crystal formations like Strontium Crystal) develop their crystals during the cooling phase, not during the firing phase. Very slow cooling through the crystal-forming range is essential.",
            "Crystal glazes containing zinc and silica in specific proportions",
            "Very slow cooling through 1800-1400°F (100-200°F per hour); crystal size and number increase with slower cooling and longer holds",
            "Faster cooling produces fewer, smaller crystals or no crystals at all. Some crystal potters program specific cooling ramps with multiple holds. The exact temperature range varies by glaze recipe — test to find the sweet spot for your specific crystal glaze. Crystal glazes are inherently runny; use catch plates.",
            "high",
        ),
        (
            "firing_effect",
            "cooling",
            "Shino carbon trapping timing",
            "Shino glazes trap carbon during the early reduction phase of firing. The carbon trapping window is tied to when the soda in the shino begins to melt and seal the surface.",
            "Shino glazes in reduction firing",
            "Soda melts around 1560°F (850°C); carbon trapping occurs as the glaze begins to melt and trap carbon from the reduction atmosphere",
            "If reduction starts too late (after the shino has fully melted), carbon cannot penetrate and you get a plain orange surface. If reduction starts too early or is too heavy, the shino may crawl. Light reduction starting around cone 012-010 with moderate reduction through cone 6-8 is typical. Each shino recipe has its own ideal reduction schedule.",
            "medium",
        ),
        (
            "firing_effect",
            "cooling",
            "Iron crystallization during cooling",
            "Iron-rich glazes can develop visible iron crystal growth during slow cooling, creating effects like tea dust and iron speckle. The crystals form as iron oxide precipitates out of the glaze melt during cooling.",
            "High-iron glazes (5%+) with slow cooling",
            "Slow cooling promotes iron crystal growth visible as green/gold/brown spots; faster cooling keeps iron dissolved for solid colors",
            "Tea dust glazes are specifically designed for this effect — they need slow cooling to develop their characteristic green and gold spots. If you want a solid iron color (like tenmoku), faster cooling actually helps. The zinc content of the glaze also affects crystallization — zinc promotes crystal growth.",
            "high",
        ),
        (
            "firing_effect",
            "cooling",
            "Tea dust specific cooling cycle",
            "Tea dust glazes require a controlled cooling cycle to develop their characteristic green and gold crystal spots on a dark base. The crystals are iron oxide that precipitates during specific temperature ranges.",
            "Tea dust or high-iron glazes with zinc",
            "Controlled slow cooling through 1800-1400°F; hold or very slow ramp allows iron crystals to grow; typical cycle: natural cool to 1800°F, then 100°F/hour to 1400°F",
            "Without the slow cooling, tea dust glazes appear as a plain dark brown/black. The green and gold spots only develop with sufficient time at the right temperature. Some tea dust recipes also benefit from a brief hold at peak temperature. Results vary by position in the kiln — cooler spots often develop better crystals.",
            "high",
        ),
        (
            "firing_effect",
            "cooling",
            "Quartz inversion zone — critical for preventing dunting",
            "At 1063°F (573°C), quartz undergoes a sudden volume change (inversion) where it expands approximately 2% on heating and contracts on cooling. Cooling too fast through this zone causes thermal shock cracking (dunting).",
            "All ceramic pieces, especially thick or uneven sections",
            "Cool slowly through 1063°F (573°C); pieces crack or shatter if cooled too fast through this zone",
            "This is the most common cause of cracking during cooling. The 2% volume change is sudden and creates enormous internal stress if the temperature differential across the piece is too large. Most kilns naturally cool slowly enough through this range, but opening the kiln too early (below 200°F is the common rule) or forced cooling can cause dunting. Thick pieces and pieces with uneven wall thickness are most vulnerable.",
            "high",
        ),
        (
            "firing_effect",
            "cooling",
            "Cristobalite conversion — delayed cracking risk",
            "At 437°F (225°C), cristobalite (a form of silica) undergoes another volume change. While less dramatic than quartz inversion, rapid cooling through this zone can cause cracking that may appear immediately or days later.",
            "Pieces that have developed cristobalite during firing (common at cone 10 with long soaks)",
            "Cool slowly through 437°F (225°C); rapid cooling can cause spontaneous cracking days or weeks after firing",
            "Cristobalite forms in silica-rich glazes and clay bodies during extended time at high temperatures. It is most common in porcelain and high-fire stoneware. The delayed cracking is especially dangerous because a piece may appear fine when unloaded from the kiln but crack during use. Avoid opening the kiln below 200°F to ensure safe passage through both the cristobalite and quartz zones.",
            "medium",
        ),
        (
            "firing_effect",
            "cooling",
            "Crash cooling effects on glaze surface",
            "Crash cooling (rapid cooling, sometimes by opening the kiln or removing peepholes at high temperature) produces a glossier surface and kills crystal development. It is the opposite of the slow cooling required for copper reds and crystal glazes.",
            "Any glaze with crash cooling or rapid cool",
            "Glossier, more glass-like surface; no crystal development; faster turnaround; increased risk of thermal shock cracking",
            "Crash cooling is useful when you want a clean glossy surface without crystal interference. It can also 'freeze' atmospheric effects like flashing or carbon trapping at a specific point. However, it will ruin copper reds, crystal glazes, and tea dust effects. Never crash cool below 1000°F — the risk of dunting is too high. Some potters crash cool from peak to ~1500°F, then slow cool for the rest.",
            "high",
        ),
        # Application methods (10)
        (
            "application_effect",
            "method",
            "Dip application — most uniform thickness",
            "Dipping is the most common and reliable glaze application method. The piece is submerged in glaze for a few seconds, producing a uniform coat with consistent thickness.",
            "Glaze mixed to dipping consistency (specific gravity ~1.4-1.5), piece submerged for 3-5 seconds",
            "Most uniform, consistent thickness; fast for production; good for full-coverage pieces",
            "Dipping requires a large volume of glaze and is difficult for very large or very small pieces. Inner surfaces of narrow forms (bottles, vases) can be tricky to coat evenly by dipping. The glaze must be well-mixed and at the right consistency — too thin and coverage is spotty, too thick and it runs. Pour any excess back into the bucket.",
            "high",
        ),
        (
            "application_effect",
            "method",
            "Brush application — variable thickness",
            "Brushing glaze applies color with a brush, producing variable thickness with visible brush marks. Best for detail work, accents, and when dip/pour is impractical.",
            "Glaze mixed to brushing consistency (specific gravity ~1.5-1.6, thicker than dipping), soft brush",
            "Variable thickness with visible brush marks; good for detail, accents, and layered effects",
            "Brushing requires thinner glaze to flow properly from the brush. Multiple thin coats give better results than one thick coat. Brush marks are usually visible on the finished piece — this can be a feature or a flaw depending on your intent. Each coat needs to dry before the next is applied. Commercial 'brush-on' glazes are formulated specifically for this method.",
            "high",
        ),
        (
            "application_effect",
            "method",
            "Spray application — thinnest coat, requires PPE",
            "Spraying applies glaze as a fine mist, producing the thinnest, most even coats. It is the best method for gradients, overlapping colors, and large pieces. Requires dedicated equipment and safety precautions.",
            "Spray gun or airbrush, glaze thinned to spraying consistency, PPE (respirator required)",
            "Thinnest, most even coat possible; excellent for gradients and color blending; good for large pieces",
            "ALWAYS wear a respirator when spraying glaze — the mist creates breathable particles. Spray in a ventilated booth or outdoors. Overspray wastes glaze and can contaminate other pieces. Multiple light passes are better than one heavy pass. Spray equipment requires cleaning after each use. This is the only method that allows true gradient effects.",
            "high",
        ),
        (
            "application_effect",
            "timing",
            "Drying between layers — prevent crawling",
            "Allowing each glaze layer to dry fully before applying the next is critical for preventing crawling and other defects. Rushing the drying time is one of the most common causes of application problems.",
            "Any layered glaze application",
            "Minimum 2-4 hours between layers; overnight drying is ideal; rushed application increases crawling risk significantly",
            "The first layer must be completely dry to the touch before applying the second. If the first layer is still damp, the water from the second layer can rewet and weaken the bond, causing the glaze to crawl during firing. In humid climates, drying takes longer. A fan can speed drying but don't point it directly at the piece. Overnight drying between layers is the safest approach.",
            "high",
        ),
        (
            "application_effect",
            "measurement",
            "Specific gravity targets for glaze consistency",
            "Specific gravity (measured with a hydrometer or by weighing a known volume) is the most reliable way to ensure consistent glaze thickness across sessions.",
            "Any glaze application",
            "Dipping: 1.4-1.5 specific gravity; Brushing: 1.5-1.6 specific gravity; Spraying: 1.3-1.4 specific gravity",
            "Specific gravity measures the ratio of glaze density to water. A 100ml graduated cylinder and a scale are all you need: weigh 100ml of glaze and divide by 100. If your glaze is too thick (high SG), add water and remix. If too thin, let it settle and pour off some water, or add more mixed glaze. Consistency in specific gravity means consistency in results.",
            "high",
        ),
        (
            "application_effect",
            "preparation",
            "Glaze settling and remixing",
            "Glaze materials have different densities and settle at different rates. Heavier materials (silica, colorants) sink to the bottom while lighter materials (clay, feldspar) stay suspended longer. A glaze that hasn't been remixed will apply unevenly.",
            "Any glaze that has been sitting unused",
            "Stir thoroughly before each use — heavier materials sink; a few minutes of stirring prevents uneven color and thickness",
            "A glaze left sitting for days may have a hard layer of settled material at the bottom that is difficult to remix. Some potters add a small amount of epsom salt (magnesium sulfate) to help keep glazes in suspension — this is called 'flocculating' the glaze. Always test application thickness after remixing, as the settled glaze may have different water content at the top vs bottom.",
            "high",
        ),
        (
            "application_effect",
            "preparation",
            "Sieving glaze for smooth surfaces",
            "Sieving glaze through a mesh screen removes lumps, unmixed materials, and debris, producing a smoother application and fewer defects in the fired surface.",
            "After mixing or remixing glaze, before application",
            "80 mesh sieve is standard for most glazes; 100 mesh or finer for smooth surfaces and spraying; removes lumps that cause pinholing and crawling",
            "A simple sieve screen over a bucket works — pour glaze through, push material through with a rubber rib. For spraying, 100 mesh or finer is important to prevent clogging the spray gun. Sieving also helps remix settled materials. Some potters sieve every time they use a glaze; others sieve only after mixing a new batch. Sieving is cheap insurance against defects.",
            "high",
        ),
        (
            "application_effect",
            "thickness_guideline",
            "Application thickness by glaze type",
            "Different glaze types perform best at different application thicknesses. Applying the wrong thickness is a common cause of glaze failure.",
            "Different glaze types",
            "Crystal glazes: thick application needed for crystal development; Shinos: thin application preferred (reduces crawling); Clear glazes: flexible, thin to medium; Textured/matte glazes: medium to thick; Glossy glazes: medium",
            "Thickness is measured in mils (thousandths of an inch) — a typical single dip coat is 3-5 mils. Too thin for a crystal glaze = no crystals. Too thick for a shino = crawling. When in doubt, test on a tile first. The target thickness is always relative to the specific glaze — follow the recipe or manufacturer's recommendation.",
            "high",
        ),
        (
            "application_effect",
            "technique",
            "Wax resist application for foot cleanup",
            "Wax resist is applied to the foot (bottom) of pieces before glazing to prevent glaze from sticking to the kiln shelf. It creates a barrier that glaze will not adhere to during application.",
            "Apply to dry bisque foot before glazing",
            "Wax resists glaze on foot; makes cleanup easy; prevents pieces from sticking to kiln shelf",
            "Apply wax to a clean, dry foot using a brush or sponge. One even coat is sufficient. Don't get wax on areas you want glazed — wax is very difficult to remove once applied. Some waxes are tinted (green or red) so you can see where you've applied. After glazing, any glaze that landed on the wax can be wiped off with a damp sponge before the wax melts during firing. Hot wax (heated in a crockpot) gives a more even coat.",
            "high",
        ),
        (
            "application_effect",
            "technique",
            "Layering wet glaze over dry layer — crawling risk",
            "Applying wet glaze over a glaze layer that has already dried completely can cause crawling. The dry layer rehydrates unevenly, creating adhesion problems.",
            "Applying fresh wet glaze over a previously applied glaze layer that has dried fully",
            "High risk of crawling — the dry layer rehydrates unevenly, causing the glaze to pull away from the surface",
            "This is one of the trickiest application challenges. If the first layer has dried hard, the safest approach is to lightly mist it with water before applying the second layer, then let it sit for a few minutes to equalize before continuing. Some potters prefer to apply both layers while the first is still slightly damp (leather-hard to the touch). This is why timing between coats matters — find the sweet spot between too wet and too dry.",
            "high",
        ),
        # Troubleshooting (7)
        (
            "troubleshooting",
            "diagnosis",
            "Crawling diagnosis — bare patches in glaze",
            "Crawling appears as bare patches where the glaze has pulled away from the surface, often with sharp or rounded edges at the margins. Diagnosis is a process of elimination.",
            "Bare patches in fired glaze, glaze receded from surface areas",
            "Check in order: (1) Was bisque dusty or greasy? Wipe with damp sponge next time. (2) Were layers applied too close together without drying? Let each dry 2-4 hours minimum. (3) Was glaze applied too thick? Thin the application. (4) Is it a Shino over non-Shino? Follow Shino layering rules. (5) Is the glaze formula too high in clay content (shrinkage mismatch)?",
            "Crawling is one of the most common glaze defects and has many causes. The most frequent culprit is dust on the bisque — always wipe pieces with a damp sponge before glazing. If crawling occurs only at edges, it may be a glaze thickness issue. If it occurs in patches, it's likely an adhesion problem. Some crawling is intentional and aesthetic — White Crawl is an example.",
            "high",
        ),
        (
            "troubleshooting",
            "diagnosis",
            "Running diagnosis — glaze on kiln shelf",
            "Running occurs when glaze flows off the piece during firing, pooling at the base or sticking to the kiln shelf. Prevention is easier than cleanup.",
            "Glaze flowed off piece, pooled at base, stuck to kiln shelf",
            "Check in order: (1) Was glaze applied too thick? Apply thinner next time. (2) Is the glaze over-fired? Check witness cones. (3) Does the glaze have a low melt point? May need kiln wash or catch plate. (4) Is the piece form too flat or horizontal? Glaze runs more on flat surfaces.",
            "Always use kiln wash on shelves to prevent sticking. For pieces known to run, place a catch plate (small clay dish) underneath. Stilts can also elevate the piece. Some running is aesthetic — tenmoku glazes are expected to run slightly. But if the piece fuses to the shelf, both are usually lost. Wadding (mixture of alumina and kaolin) under the foot can also protect the shelf.",
            "high",
        ),
        (
            "troubleshooting",
            "diagnosis",
            "Pinholing diagnosis — small pits in glaze surface",
            "Pinholing appears as small pits or holes in the glaze surface, like tiny craters. These are caused by gas escaping during firing that doesn't heal over before the glaze sets.",
            "Small pits or holes in fired glaze surface, rough to the touch",
            "Check in order: (1) Is bisque underfired? Fire bisque to cone 04 instead of cone 06 — this burns out more organic material. (2) Was firing too fast? Slow the rate, especially through 1000-1500°F. (3) Is glaze too thin? Apply slightly thicker. (4) Was there a hold at peak temperature? A 15-30 minute hold lets the glaze level and heal over. (5) Is the clay body high in organic material or grog?",
            "Pinholing is often a combination of issues. The most effective fix is usually hotter bisque + hold at peak. If pinholing persists, try a slightly different glaze application thickness. Some clay bodies are more prone to pinholing than others — bodies with high grog content or organic material can outgas more. A glaze with more fluid melt (more flux) may heal over pinholes better than a stiff melt.",
            "high",
        ),
        (
            "troubleshooting",
            "diagnosis",
            "Crazing diagnosis — crackle pattern in glaze",
            "Crazing is a fine spider-web crack pattern in the glaze surface. While sometimes intentional, unexpected crazing indicates a fit problem between glaze and clay body.",
            "Fine crackle pattern in glaze, may appear immediately or develop over weeks/months",
            "Check in order: (1) Is the glaze COE (coefficient of thermal expansion) too high for the clay body? Switch to a better-matched glaze or adjust the recipe. (2) Did the kiln cool too fast? Slow cooling reduces crazing. (3) Is the piece thin-walled? Thin pieces are more susceptible. (4) Was the glaze applied too thick? Thinner application reduces stress.",
            "To fix crazing long-term, the COE of the glaze must be reduced relative to the clay body. In the glaze recipe: increase silica (raises COE slightly but strengthens glaze), increase alumina (lowers COE), reduce high-expansion fluxes (sodium, potassium) in favor of low-expansion fluxes (boron, lithium, magnesium). Crazing that appears weeks later (delayed crazing) is caused by moisture absorption expanding the clay body — the mismatch was always there.",
            "high",
        ),
        (
            "troubleshooting",
            "diagnosis",
            "Shivering diagnosis — glaze popping off clay body",
            "Shivering is the opposite of crazing — the glaze COE is too LOW relative to the clay body, causing the glaze to pop off in chips or flakes. It is less common than crazing but more dangerous because sharp glaze fragments can break off during use.",
            "Glaze flaking or popping off the clay body in chips, sharp edges",
            "Check in order: (1) Is the glaze COE too low? Increase sodium/potassium fluxes or reduce silica/alumina. (2) Is the glaze applied too thin? Thin application is more prone to shivering. (3) Is the clay body high in thermal expansion? Some bodies don't pair well with low-COE glazes. (4) Did the piece cool too fast? Rapid cooling can trigger shivering.",
            "Shivering is dangerous on functional ware because sharp flakes can break off into food. Unlike crazing (which is mainly a food safety concern), shivering creates an immediate physical hazard. If you see shivering, do not use the piece for food. The fix is opposite to crazing: increase glaze COE by adding high-expansion fluxes (soda, potash) or reducing silica and alumina.",
            "high",
        ),
        (
            "troubleshooting",
            "diagnosis",
            "Color off diagnosis — unexpected glaze color",
            "When a glaze fires to an unexpected color, the cause is usually atmospheric, chemical, or material. Diagnosis requires understanding what colorants are in the glaze and what affects them.",
            "Glaze fired to unexpected color — wrong hue, too dark, too light, muddy",
            "Check in order: (1) Copper glaze went green instead of red? Reduction failed or was too light. (2) Pink/magenta turned brown? Zinc in the base glaze — chrome-tin pinks need zinc-free bases. (3) Color is muddy or washed out? Too many colorants interacting, or iron in the clay body affecting translucent glazes. (4) Color varies across piece? Uneven atmosphere or thickness variation. (5) Color is too dark? Applied too thick or overfired.",
            "The most common color surprise is copper reds turning green — this is almost always a reduction issue. Pink turning brown is almost always a zinc issue. Iron showing through translucent glazes is normal for iron-bearing clay bodies. Keep notes on what works and what doesn't for each glaze in your kiln — position matters.",
            "high",
        ),
        (
            "troubleshooting",
            "diagnosis",
            "Dunting diagnosis — cracking during cooling",
            "Dunting is cracking that occurs during cooling, often with an audible ping or pop. It is caused by thermal shock when the piece cools too fast through critical temperature zones.",
            "Crack appeared during cooling, often sudden with audible sound",
            "Check in order: (1) Did the kiln cool too fast through 1000-1100°F? This is the quartz inversion zone — slow cool here. (2) Is the piece thick-walled or uneven? Thick sections cool unevenly and crack. (3) Was the kiln opened too early? Wait until below 200°F before opening. (4) Is the clay body high in quartz? Some bodies are more prone to dunting.",
            "Dunting cracks are usually clean, sharp breaks (different from cracking during drying which produces jagged edges). The crack often runs through both glaze and body. Once dunted, the piece cannot be repaired. Prevention is the only approach: slow cooling through 1000-1100°F (hold for 30-60 minutes), avoid thick sections, and never open a hot kiln. Pieces near vents or peepholes are more vulnerable to dunting.",
            "high",
        ),
        # UMF interpretation (6)
        # Sources: Digitalfire, Ceramic Arts Network, Alfred University (Carty/Katz 2008),
        # Ceramic Materials Workshop, Glazy.org
        (
            "umf_interpretation",
            "ratio",
            "Silica:Alumina ratio predicts glaze surface",
            "The ratio of SiO2 to Al2O3 in the Unity Molecular Formula is the primary predictor of glaze surface quality. This is well-established ceramic science confirmed by research at Alfred University and published in Ceramic Arts Network.",
            "UMF SiO2:Al2O3 ratio",
            "Below 3:1 = underfired or dry matt; 3:1 to 5:1 = matt; 5:1 to 10:1 = glossy; above 10:1 = runny",
            "These ratios are guidelines for cone 8-10. At lower temperatures the same ratio produces a different surface. Other factors (flux type, cooling rate, firing atmosphere) also affect the result. Adding silica to a matte glaze can shift it toward glossy without changing other oxides (Sue McLeod, Ceramic Arts Network 2023).",
            "high",
        ),
        (
            "umf_interpretation",
            "ratio",
            "Flux:Alumina ratio predicts melt behavior",
            "The ratio of total fluxes to alumina indicates whether a glaze will melt properly, be underfired, or run excessively. Source: Digitalfire limit formulas and Ceramic Materials Workshop UMF education.",
            "UMF total fluxes (sum = 1.0) divided by Al2O3",
            "Below 2:1 = dry, underfired appearance; 2:1 to 3:1 = stable melt with good surface; above 3:1 = runny, potential defects",
            "This ratio interacts with the SiO2:Al2O3 ratio. A glaze can have a good flux:alumina ratio but still be problematic if silica is too low. Always check both ratios together.",
            "high",
        ),
        (
            "umf_interpretation",
            "flux_type",
            "Alkali vs alkaline earth flux ratio affects expansion and surface",
            "The balance between alkali fluxes (K2O, Na2O) and alkaline earth fluxes (CaO, MgO, BaO, SrO, ZnO) affects thermal expansion, melt fluidity, and surface character. Source: Digitalfire and standard ceramic engineering texts.",
            "Ratio of alkali (KNaO) to alkaline earth fluxes in UMF",
            "High alkali (KNaO > 0.5): higher thermal expansion, more fluid, brighter colors, prone to crazing. Balanced (KNaO 0.2-0.4): most common for stable glazes. High alkaline earth (CaO+MgO > 0.7): lower expansion, stiffer melt, promotes matte surfaces",
            "Alkali fluxes (potassium, sodium) produce higher thermal expansion than alkaline earth fluxes (calcium, magnesium). This is why high-feldspar glazes craze more than high-whiting glazes. The alkali:alkaline earth ratio is sometimes called the 'flux ratio' and is a key diagnostic for fit problems.",
            "high",
        ),
        (
            "umf_interpretation",
            "stability",
            "UMF limit formulas for cone 10 glaze stability",
            "Limit formulas define the acceptable range of each oxide in the UMF for a glaze to be stable, durable, and properly melted at a given temperature. Recipes outside limits are prone to defects. Source: Digitalfire limit formulas, widely used in ceramic education.",
            "Cone 8-10 temperature range",
            "KNaO: 0.1-0.5; CaO: 0.2-0.8; MgO: 0.0-0.4; BaO: 0.0-0.3 (toxic); Al2O3: 0.2-0.5; SiO2: 2.5-5.0; B2O3: 0.0-0.3",
            "Limit formulas are guidelines, not absolute rules. Some successful glazes operate near or slightly outside limits. However, glazes far outside limits are almost always problematic. Alfred University research (Carty/Katz 2008) noted that traditional limit formulas can be 'over-simplified' but remain useful starting points for glaze development.",
            "medium",
        ),
        (
            "umf_interpretation",
            "diagnosis",
            "Reverse engineering glaze behavior from UMF",
            "When a glaze exhibits a specific behavior problem (crazing, running, crawling, matte when glossy is wanted), the UMF reveals the likely cause and fix. Source: reverse-engineering.md, Digitalfire, Ceramic Arts Network.",
            "Observed glaze defect + UMF analysis",
            "Crazing: SiO2 below 3.0 or high KNaO → increase silica, reduce feldspar. Matt when glossy wanted: Al2O3 above 0.4 → substitute some kaolin for silica. Running: SiO2 below 2.5 or high boron → increase alumina, reduce flux. Crawling: low Al2O3, high surface tension → add clay (EPK), reduce boron. Pinholing: too fluid or underfired → adjust flux, verify firing.",
            "These are starting-point diagnostics, not guaranteed fixes. Multiple factors can cause the same defect. Always test changes on small batches before committing to a full glaze adjustment.",
            "medium",
        ),
        (
            "umf_interpretation",
            "method",
            "UMF calculation method overview",
            "The Unity Molecular Formula converts a recipe (measured in weight) to a molecular ratio formula where fluxes total 1.0. This allows direct comparison between any two glazes regardless of recipe size. Source: Ceramic Arts Network (Linda Bloomfield 2022), Ceramic Materials Workshop, Glazy.org.",
            "Any glaze recipe with known material analyses",
            "Step 1: Convert each material's weight percentage to oxide moles using molecular weights. Step 2: Sum all flux oxide moles (K2O, Na2O, CaO, MgO, ZnO, BaO, etc.). Step 3: Divide ALL oxide amounts by the total flux sum. Result: fluxes = 1.0, Al2O3 and SiO2 shown relative to flux.",
            "Molecular weights needed: SiO2=60.1, Al2O3=101.8, K2O=94.2, Na2O=62.0, CaO=56.1, MgO=40.3, ZnO=81.4, BaO=153.3, B2O3=69.6. Online tools like Glazy.org calculate UMF automatically from recipes. You do NOT need to calculate by hand unless you want to understand the process.",
            "high",
        ),
        # Material substitution (7)
        # Sources: glaze-chemistry.md, Glazy.org substitution guide, Ceramic Arts Network
        (
            "material_substitution",
            "colorant",
            "Cobalt oxide vs carbonate substitution",
            "Cobalt oxide (Co3O4) and cobalt carbonate (CoCO3) supply cobalt at different concentrations. When substituting, adjust the weight to maintain equivalent CoO. Source: glaze-chemistry.md (molecular weight analysis), Glazy.org.",
            "Recipe calls for cobalt oxide but only carbonate available, or vice versa",
            "Cobalt oxide → cobalt carbonate: multiply by 1.48 (oxide is 93% CoO, carbonate is 63% CoO). Cobalt carbonate → cobalt oxide: multiply by 0.68.",
            "Cobalt is extremely powerful — even small errors produce visible color differences. Mix a test batch first. The carbonate form disperses more evenly in the glaze, which can produce more consistent color in some bases.",
            "high",
        ),
        (
            "material_substitution",
            "colorant",
            "Copper oxide vs carbonate substitution",
            "Copper oxide (CuO) and copper carbonate (CuCO3) supply copper at different concentrations. Source: glaze-chemistry.md.",
            "Recipe calls for copper oxide but only carbonate available, or vice versa",
            "Copper oxide → copper carbonate: multiply by 1.55 (oxide is ~100% CuO, carbonate is ~64-65% CuO). Copper carbonate → copper oxide: multiply by 0.64.",
            "Copper carbonate decomposes during firing, releasing CO2. In thick application this can cause pinholing or blistering. Copper oxide is sometimes preferred for this reason. Both produce identical final color when properly fired.",
            "high",
        ),
        (
            "material_substitution",
            "colorant",
            "Manganese dioxide vs carbonate substitution",
            "Manganese dioxide (MnO2) and manganese carbonate (MnCO3) supply manganese at different concentrations. Source: glaze-chemistry.md.",
            "Recipe calls for manganese dioxide but only carbonate available, or vice versa",
            "Manganese dioxide → manganese carbonate: multiply by 1.62 (dioxide is ~100% effective MnO, carbonate is ~61-62% MnO). Manganese carbonate → manganese dioxide: multiply by 0.62.",
            "Manganese carbonate disperses more evenly and may produce slightly different color results due to more uniform distribution. Both forms are neurotoxic — always wear a respirator when handling either form.",
            "high",
        ),
        (
            "material_substitution",
            "flux",
            "Whiting vs wollastonite substitution",
            "Whiting (CaCO3) and wollastonite (CaSiO3) both supply calcium but wollastonite also contributes silica. Source: glaze-chemistry.md, Ceramic Arts Network.",
            "Recipe calls for whiting but only wollastonite available, or vice versa",
            "Whiting → wollastonite: multiply by 1.16 (whiting is 56% CaO, wollastonite is 48% CaO + 52% SiO2). Wollastonite → whiting: multiply by 0.86. IMPORTANT: when substituting wollastonite for whiting, reduce the silica in the recipe by approximately 6% to compensate for the silica wollastonite contributes.",
            "Wollastonite is often preferred for its lower loss on ignition (LOI), which reduces glaze shrinking during drying and lessens pinholing risk. However, the silica contribution must be accounted for or the glaze will become glossier than intended.",
            "high",
        ),
        (
            "material_substitution",
            "flux",
            "Barium vs strontium substitution",
            "Barium carbonate (BaCO3) and strontium carbonate (SrCO3) are chemically related alkaline earth fluxes with similar but not identical effects. Source: glaze-chemistry.md, Ceramic Arts Network (Dave Finkelnburg).",
            "Recipe calls for barium carbonate but want to avoid barium toxicity",
            "Barium carbonate → strontium carbonate: multiply by 0.75 (BaCO3 is 77.5% BaO, SrCO3 is 70% SrO). Strontium carbonate → barium carbonate: multiply by 1.33. Strontium is LESS toxic than barium.",
            "Strontium is generally considered safer than barium for food-contact surfaces, though both should be tested. Strontium tends to produce slightly different surface qualities — it promotes crystal growth more readily than barium. Dave Finkelnburg (Ceramic Arts Network) notes the substitution is close but not exact in all glaze bases.",
            "medium",
        ),
        (
            "material_substitution",
            "feldspar",
            "Feldspar substitution principles",
            "Feldspars are the primary flux source in most glazes. Substitution between feldspars requires matching oxide contributions. Source: glaze-chemistry.md, Glazy.org substitution guide, Ceramic Arts Network (Jeff Zamek).",
            "Need to substitute one feldspar for another",
            "Substitute ONLY within the same group: Potash group (Custer, G-200, K200, Primas P) can substitute for each other. Soda group (Kona F-4, Nepheline Syenite, Calspar, NC-4) can substitute for each other. CRITICAL: Nepheline syenite is NOT a direct substitute for potash feldspar — it has lower silica and higher alumina.",
            "Even within the same group, feldspars have different analyses. Custer and G-200 are both potash feldspars but G-200 has slightly more silica and less alumina. This can produce subtle surface differences. Always test substitutions on a small batch. Jeff Zamek (Ceramic Arts Network) notes that economic forces frequently make feldspars obsolete — the skill of substitution is essential for long-term studio practice.",
            "high",
        ),
        (
            "material_substitution",
            "complex",
            "Gerstley borate and Albany slip replacements",
            "Two historically important ceramic materials are no longer mined: Gerstley Borate (calcium borate ore) and Albany Slip (natural clay). Source: glaze-chemistry.md, Ceramic Arts Network.",
            "Recipe calls for Gerstley Borate or Albany Slip",
            "Gerstley Borate replacements: Colemanite (calcium borate), boron frits (e.g., Ferro 3134), or calcined borax. Note: both Gerstley Borate and Colemanite are naturally variable materials. Albany Slip replacements: Alberta Slip, Seattle Slip, Sheffield Slip Clay Formula, or A.R.T. Albany Slip Synthetic. Matching depends on amount in recipe, temperature, and atmosphere.",
            "These replacements are approximate. Albany Slip was a unique natural clay and no synthetic perfectly replicates it — results vary by percentage used in the recipe, firing temperature, and atmosphere. Test on small batches. Many potters maintain separate recipe versions for each substitute.",
            "medium",
        ),
        # Clay body interaction (4)
        # Sources: Ceramics International (Gol et al. 2021), Journal of European Ceramic Society
        # (Valancience et al. 2010), PMC/MDPI (Wu et al. 2024), standard ceramic texts
        (
            "clay_body_interaction",
            "iron",
            "Iron in clay body affects translucent glaze color",
            "Iron oxide present in the clay body will show through translucent glazes, shifting their color. This is a well-documented effect in ceramic science. Source: Journal of European Ceramic Society (Valancience et al. 2010), published research on iron-series glazed wares.",
            "Any translucent or semi-transparent glaze over an iron-bearing clay body",
            "Translucent glazes over iron-bearing clay will appear darker, warmer, or more amber than the same glaze over a white clay body. The effect is proportional to both the iron content in the clay and the translucency of the glaze.",
            "This is why the same celadon glaze looks different on porcelain (white, low iron) vs stoneware (grey-brown, higher iron). If you want the 'true' color of a translucent glaze, test it on a white clay body. Some potters intentionally choose iron-bearing bodies for warmer glaze tones.",
            "high",
        ),
        (
            "clay_body_interaction",
            "iron",
            "Iron content in clay body darkens with firing temperature",
            "Research confirms that increasing firing temperature causes iron in clay bodies to convert from structural forms to hematite (Fe2O3), darkening the body color. Source: Journal of European Ceramic Society (Valancience et al. 2010) — iron in hematite increases 5x between 600-1025°C.",
            "Iron-bearing clay body fired to higher temperatures",
            "As firing temperature increases from 600°C to 1025°C+, iron converts to hematite, darkening the clay body from light buff to reddish brown. This affects any glaze applied over the body, especially translucent glazes.",
            "The darkening effect depends on iron content, firing atmosphere, and soak time. In reduction firing, iron in the body can produce grey to black colors rather than red-brown. The body color beneath the glaze is a permanent part of the visual result — it cannot be adjusted after firing.",
            "high",
        ),
        (
            "clay_body_interaction",
            "absorption",
            "Clay body porosity affects glaze application and fit",
            "The porosity of the bisque-fired clay body determines how much glaze it absorbs during application. This affects both the thickness achieved and the glaze-body bond. Source: standard ceramic engineering principles.",
            "Different clay bodies with different bisque porosity",
            "Higher porosity (e.g., earthenware bisque at cone 06) absorbs glaze quickly and deeply, making it easy to build thickness. Lower porosity (e.g., high-fire stoneware bisque) absorbs less glaze, requiring thinner application or multiple coats. Porosity also affects glaze fit — a very porous body can allow glaze to penetrate deeply, creating a stronger bond.",
            "The same glaze applied to high-porosity and low-porosity bisque will fire differently because of thickness differences. When switching clay bodies, always re-test glaze application to achieve the same fired thickness. Porosity is measured by water absorption test: (saturated weight - dry weight) / dry weight × 100.",
            "high",
        ),
        (
            "clay_body_interaction",
            "thermal_expansion",
            "Clay body thermal expansion must match glaze for fit",
            "The thermal expansion of the clay body determines what glazes will fit without crazing or shivering. Different clay bodies have different thermal expansion values. Source: standard ceramic engineering, Digitalfire.",
            "Any glaze applied to a new or different clay body",
            "Each clay body has a specific coefficient of thermal expansion (CTE). A glaze that fits one body perfectly may craze on a body with lower expansion or shiver on a body with higher expansion. There is no universal 'food-safe' glaze — fit depends on the specific body-glaze combination.",
            "When switching clay bodies, always test existing glazes for fit. Quick test: apply glaze to a tile of the new body, fire, then thermal shock test (boil for 5 min, ice bath for 5 min, repeat 3x). If crazing appears, the glaze CTE is too high for that body. If shivering appears, the glaze CTE is too low.",
            "high",
        ),
        # Surface quality from chemistry (4)
        # Sources: Ceramic Arts Network (Sue McLeod 2023), Springer Nature (Serkan 2024),
        # Digitalfire, prediction-framework.md
        (
            "surface_quality",
            "gloss_matt",
            "Converting matte to glossy by adjusting silica",
            "Adding silica (SiO2) to a matte glaze can convert it to glossy, because increasing the SiO2:Al2O3 ratio shifts the glaze from the matte zone toward the glossy zone. Source: Ceramic Arts Network (Sue McLeod, 'Matte to Glossy' 2023), Springer Nature (Serkan et al. 2024 — SiO2/Al2O3 ratio study on porcelain tile glazes).",
            "Matte glaze that you want to be glossier",
            "Add silica incrementally until the desired surface is achieved. Sue McLeod demonstrated that adding 40g silica per 100g of a matte glaze base (keeping all other materials constant) converted it from matte to glossy. The SiO2:Al2O3 ratio must move from the matte zone (3-5:1) toward the glossy zone (5-10:1).",
            "This only works if the glaze has adequate flux to melt the additional silica. If you add too much silica without adjusting flux, the glaze may become underfired. Springer research (Serkan et al. 2024) confirmed that as SiO2/Al2O3 ratio decreases, anorthite crystal increases, producing matte surfaces — the reverse is also true.",
            "high",
        ),
        (
            "surface_quality",
            "gloss_matt",
            "High alumina creates matte surfaces",
            "Alumina (Al2O3) acts as a stabilizer in glazes. High alumina content prevents the glaze from flowing flat, creating a matte surface with microscopic crystal structure. Source: prediction-framework.md, Digitalfire, standard ceramic science.",
            "Glaze with Al2O3 above 0.4 in UMF (cone 8-10)",
            "High alumina content produces matte surfaces because alumina raises the melting point and stiffens the melt, preventing it from leveling into a smooth glossy surface. The surface appears soft-matt to dry-matt depending on the exact ratio and other oxides.",
            "To convert a matte glaze to glossy, the standard approach is to reduce alumina (use less clay/kaolin) and increase silica. Alternatively, increase flux content to melt the alumina more fully. Pure alumina mattes are among the most durable and food-safe matte surfaces because the high alumina provides chemical resistance.",
            "high",
        ),
        (
            "surface_quality",
            "opacity",
            "Opacity control: tin, zirconium, and titanium",
            "Three primary materials create opacity in ceramic glazes, each through different mechanisms. Source: standard ceramic chemistry, Digitalfire material reference.",
            "Need to create opaque or semi-opaque glaze",
            "Tin oxide (5-15%): produces the whitest, most opaque surface but is expensive. Zirconium silicate (Zircopax, 10-20%): effective opacifier, less expensive than tin, slightly blue-white tone. Titanium dioxide (5-10%): opacifies and promotes variegation/crystal formation, can produce blue-white or creamy tones depending on other oxides.",
            "Zinc oxide can also contribute opacity in some bases. Rutile (titanium + iron) produces subtle variegated opacity rather than full white. The choice of opacifier affects not just opacity but also color response — chrome-tin pinks require tin, while zirconium can make some colors slightly cooler.",
            "high",
        ),
        (
            "surface_quality",
            "flux_effect",
            "Calcium and magnesium promote different matte surfaces",
            "Calcium and magnesium both produce matte surfaces but through different mechanisms and with different aesthetic results. Source: prediction-framework.md, Digitalfire, Ceramic Arts Network.",
            "Glaze formulation with high calcium or magnesium content",
            "Calcium-dominated glazes (high CaO in UMF): produce smooth, buttery satin-matte surfaces. Calcium matte glazes are among the most common and reliable matte surfaces. Magnesium-dominated glazes (high MgO): produce drier, more tactile matte surfaces. Magnesium can promote crystal growth (especially with zinc present) creating speckled or woolly matte effects.",
            "High magnesium can make glazes more prone to crawling because magnesium increases surface tension. The calcium:magnesium ratio is a useful adjustment — more calcium for smooth satin, more magnesium for dry tactile surfaces. Both are alkaline earth fluxes with lower thermal expansion than alkali fluxes.",
            "high",
        ),
        # Kiln troubleshooting (4)
        # Sources: firing-guide.md, L&L Kilns (hotkilns.com), KilnFrog, Paragon Industries
        (
            "kiln_troubleshooting",
            "diagnosis",
            "Firing too slow — causes and solutions",
            "When a kiln fires progressively slower than expected or cannot reach target temperature, the most common cause is aging heating elements. Source: L&L Kilns (hotkilns.com), KilnFrog (element troubleshooting guide), Paragon Industries.",
            "Kiln takes longer than usual or cannot reach target cone",
            "Diagnosis in order of likelihood: (1) Aging elements — elements gradually increase resistance as they oxidize, producing less heat. Check with multimeter. (2) Low voltage — seasonal voltage drops (summer brownouts) or other appliances on the same circuit. Check voltage at the kiln during firing. (3) Overloading — too much mass or too many shelves slow the kiln. Space shelves to allow heat flow. (4) Lid not sealing — heat escapes through gaps.",
            "Elements typically last 100-300 firings depending on temperature and atmosphere. Gas kiln elements last longer than electric. KilnFrog notes that aging elements 'expand and grow,' which can actually decrease resistance temporarily before it increases. The gradual slowdown is the key symptom — a sudden change points to relay failure or voltage problems.",
            "high",
        ),
        (
            "kiln_troubleshooting",
            "diagnosis",
            "Firing too fast — causes and solutions",
            "When a kiln fires faster than the programmed schedule, pieces may be underfired (glaze defects) or thermal shock may crack ware. Source: firing-guide.md.",
            "Kiln reaches temperature before the programmed time",
            "Common causes: (1) New elements — fresh elements produce more heat than aged ones. (2) Higher voltage than expected — check voltage. (3) Light load — a kiln with few pieces heats faster. (4) Incorrect controller settings — verify the program matches your intended schedule.",
            "A fast-firing kiln can be compensated by adjusting the controller to slower ramps. However, if the kiln fires fast AND your glazes are turning out well, you may simply have an efficient setup. The issue is only when fast firing causes defects or underfiring. Always trust witness cones over the controller — the cone measures actual heatwork regardless of speed.",
            "high",
        ),
        (
            "kiln_troubleshooting",
            "diagnosis",
            "Temperature gradient in kiln — hot and cold spots",
            "Temperature varies within any kiln — the top, bottom, sides, and center all fire slightly differently. Understanding and managing this gradient is essential for consistent results. Source: firing-guide.md, standard kiln operation practice.",
            "Glazes on some shelves fire differently than others",
            "Use witness cones at multiple levels (top, middle, bottom) to map your kiln's gradient. Common patterns: top of updraft kiln is hotter, bottom is cooler; center of electric kiln is most even; areas near elements may be hotter. Solutions: (1) Rotate shelf positions between firings. (2) Add hold time at peak to allow temperature to equalize. (3) Adjust loading — don't put all important pieces in the hot spot. (4) Use setter pads to elevate pieces in cold zones.",
            "Gas kilns typically have more gradient than electric. A 1-2 cone difference between top and bottom is common in gas kilns. Electric kilns with 3-zone controllers reduce but don't eliminate gradient. Understanding YOUR specific kiln's pattern through witness cone records is more valuable than any general advice.",
            "high",
        ),
        (
            "kiln_troubleshooting",
            "programming",
            "Kiln controller programming basics",
            "Understanding how to program a kiln controller is essential for custom firing schedules, controlled cooling, and special glaze effects. Source: firing-guide.md.",
            "Need to program a custom firing schedule",
            "Controllers have two modes: (1) Cone Fire mode — select a cone and speed, controller handles temperatures automatically. Good for standard firings. (2) Ramp/Hold mode — specify exact ramp rates (°F/hr), target temperatures, and hold times. Required for controlled cooling, custom schedules, and special effects. Key segments for cone 10 reduction: initial drying (80-150°F/hr to 250°F), water smoking (200-300°F/hr to 1000°F), quartz inversion slow (100-150°F/hr to 1100°F), main ramp (300-400°F/hr), final approach (40-120°F/hr), peak hold (10-30 min), controlled cool (200-500°F/hr).",
            "Different controller brands (Skutt, L&L, Bartlett, Orchard) have different interfaces but all use the same ramp/hold concepts. When programming in Fahrenheit, the controller handles the conversion to Celsius internally if set to °C display. Always write down your schedule — controller memory can be lost during power outages.",
            "high",
        ),
        # Glaze mixing (4)
        # Sources: Ceramic Materials Workshop, Seattle Pottery Supply, Laima Ceramics
        (
            "glaze_mixing",
            "process",
            "Glaze mixing process from dry recipe",
            "Mixing a glaze from a dry recipe requires precise measurement, thorough blending, and proper sieving. Source: Ceramic Materials Workshop (glaze mixing guide), Seattle Pottery Supply (dry glaze mixing instructions).",
            "Converting a dry recipe to liquid glaze for application",
            "Process: (1) Weigh each dry ingredient accurately on a digital scale. (2) Combine all dry ingredients and mix thoroughly BEFORE adding water (dry blending). (3) Add water gradually — start with roughly 80-100g water per 100g dry glaze as a starting point. (4) Stir thoroughly, scraping sides. Let sit overnight for best results. (5) Sieve through 80 mesh (or 100 mesh for smooth surfaces). (6) Measure specific gravity and adjust with water: 1.4-1.5 for dipping, 1.5-1.6 for brushing.",
            "Always wear a respirator when handling dry glaze materials — silica dust is the primary hazard. Use non-reactive containers (plastic or stainless steel). Some glazes benefit from a deflocculant (epsom salt) if they settle excessively. Record the specific gravity of every batch for consistency.",
            "high",
        ),
        (
            "glaze_mixing",
            "water",
            "Water ratio and specific gravity for glaze consistency",
            "The amount of water in a glaze determines its application thickness. Too much water = thin, unreliable coats. Too little = thick, prone to crawling. Source: Laima Ceramics (glaze mixing guidelines), Ceramic Materials Workshop.",
            "Adjusting glaze water content for application",
            "Start with approximately 8-10 parts water to 10 parts dry glaze powder by weight. Adjust to reach target specific gravity: dipping 1.40-1.50, brushing 1.50-1.60, spraying 1.30-1.40. Always start thicker and add water — if too thin, let settle and pour off excess water from the top after a few hours. Measure SG with a hydrometer or by weighing 100ml of glaze (should weigh 140-160g depending on target).",
            "The same glaze formula can produce very different results depending on water content. A glaze mixed to SG 1.40 vs 1.50 will have noticeably different fired thickness. This is why recording SG is as important as recording the recipe. Glazes settle over time — always stir thoroughly and re-measure SG before each use.",
            "high",
        ),
        (
            "glaze_mixing",
            "testing",
            "Test tile methodology for glaze evaluation",
            "Systematic testing on tiles is the foundation of glaze development. Without controlled tests, changes are guesswork. Source: reverse-engineering.md (5-step workflow), standard ceramic practice.",
            "Evaluating a new or modified glaze recipe",
            "Method: (1) Mix a small test batch (100-200g dry). (2) Apply to test tiles made from YOUR production clay body — body matters for fit and color. (3) Apply multiple thicknesses on each tile (thin, medium, thick) to see the full range. (4) Fire with witness cones to verify actual temperature. (5) Document: recipe, SG, application method, firing schedule, cone reached, position in kiln. (6) Compare results to target. (7) Adjust one variable at a time. Never change two things between tests.",
            "Test tiles should ideally be flat, with a texture sample on one half (to see how the glaze breaks over texture) and smooth on the other half. Some potters use a vertical tile to see how the glaze runs. Always fire test tiles in the same zone of the kiln for consistency — top, middle, and bottom can produce different results.",
            "high",
        ),
        (
            "glaze_mixing",
            "storage",
            "Glaze storage and shelf life",
            "Proper storage extends glaze life and maintains consistency. Improperly stored glazes can spoil, settle into hard cakes, or grow mold. Source: standard studio practice.",
            "Storing mixed glaze between uses",
            "Keep mixed glaze in sealed plastic containers with tight-fitting lids. Label with: glaze name, recipe ID, date mixed, SG at mixing, and any modifications. Stir thoroughly before each use — heavier materials settle. If glaze develops mold (common in organic binders like CMC), add a few drops of bleach or hydrogen peroxide. Glazes do not 'expire' chemically, but they can change due to evaporation (add water) or contamination (keep containers clean). Dry glaze materials stored in sealed containers in a dry environment last indefinitely.",
            "CMC (carboxymethyl cellulose) gum, added to brushing glazes as a binder, is organic and can mold. Commercial brushing glazes contain preservatives. If mixing your own brushing glaze with CMC, add a preservative or keep refrigerated. Glaze that has dried out can be reconstituted with water, but the reconstituted version may have slightly different properties than the original.",
            "medium",
        ),
        # Ergonomics (3)
        # Sources: material-safety.md (OSHA ergonomic standards), OSHA 29 CFR 1910
        (
            "ergonomics",
            "workstation",
            "Pottery studio workstation height requirements",
            "Proper workstation height reduces back strain, shoulder injury, and fatigue during extended glazing and throwing sessions. Source: OSHA ergonomic standards cited in material-safety.md.",
            "Setting up or evaluating a pottery workspace",
            "Minimum working height: 27.6 inches. Maximum working height: 56.2 inches. The purpose is to eliminate overhead reaching and excessive bending. Store frequently used materials (glazes, tools) at waist height. Use adjustable-height stools for throwing. Personalize wheel height and stool height for each user — one size does not fit all.",
            "These are OSHA general ergonomic guidelines. Individual comfort varies. The key principle is: the most-used items and activities should be at the most comfortable height (roughly elbow height for standing work). If you find yourself reaching up or bending down frequently, rearrange your workspace.",
            "high",
        ),
        (
            "ergonomics",
            "handling",
            "Material handling safety in pottery studio",
            "Ceramic materials are heavy — bags of clay (25-50 lbs), buckets of glaze, and kiln shelves all require proper lifting technique. Source: OSHA standards cited in material-safety.md.",
            "Moving heavy materials in the studio",
            "Eliminate lifting items over 50 pounds. Use carts for heavy materials (clay, glaze buckets, kiln shelves). Store frequently used materials at waist height to minimize bending. Use scissor lift tables to reduce bending when accessing low storage. Provide a faucet hose extension to eliminate lifting heavy water buckets. When lifting is necessary: bend at the knees, keep the load close to your body, and avoid twisting while carrying.",
            "The most common pottery injuries are repetitive strain (from throwing/glazing for hours) and back injuries (from lifting clay bags and kiln shelves). Both are preventable with proper setup and technique. Investing in good shelving, carts, and lifting aids pays for itself in avoided injuries.",
            "high",
        ),
        (
            "ergonomics",
            "repetitive_motion",
            "Repetitive motion prevention for potters",
            "Pottery involves highly repetitive motions — throwing, wedging, glazing, trimming — that can cause repetitive strain injuries over time. Source: OSHA ergonomic standards cited in material-safety.md.",
            "Extended pottery work sessions (throwing, glazing, trimming)",
            "Do not perform the same repetitive activity in long unbroken sessions. Vary tasks throughout the day — alternate between throwing, trimming, glazing, and cleanup. Take regular breaks every 45-60 minutes. Use adjustable stools with lumbar support for seated work. Personalize wheel and stool heights for each user — proper posture reduces strain. Watch for early warning signs: tingling, numbness, aching in wrists, hands, or shoulders.",
            "Repetitive strain injuries develop gradually and can become chronic if ignored. Carpal tunnel syndrome and tendonitis are common among production potters. Prevention is far easier than treatment. If you experience persistent pain, stop the aggravating activity and consult a medical professional. Ergonomic tool handles (larger diameter, cushioned grips) can reduce hand strain.",
            "high",
        ),
    ]

    # Merge with external chemistry-rules.json if available (external data takes precedence)
    try:
        from core.chemistry.data_loader import load_chemistry_rules

        external_rules = load_chemistry_rules()
        if external_rules:
            # Convert JSON rules to tuple format and prepend (they override matching hardcoded rules)
            external_tuples = []
            for r in external_rules:
                external_tuples.append(
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
                )
            # Build set of (category, subcategory, name) from external rules
            external_keys = {(r[0], r[1], r[2]) for r in external_tuples}
            # Filter out hardcoded rules that are superseded by external ones
            filtered_hardcoded = [
                r for r in chemistry_rules if (r[0], r[1], r[2]) not in external_keys
            ]
            chemistry_rules = external_tuples + filtered_hardcoded
            logger.info(
                f"Loaded {len(external_tuples)} chemistry rules from ceramics-foundation, {len(filtered_hardcoded)} from defaults"
            )
    except ImportError:
        logger.debug(
            "ceramics-foundation data_loader not available, using hardcoded chemistry rules"
        )

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
