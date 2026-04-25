"""
Authentication Middleware for OpenGlaze Cloud Mode
Flask decorators and middleware for secure authentication.
"""

import os
import logging
import functools
from typing import Optional, Callable
from flask import request, g, jsonify

logger = logging.getLogger(__name__)

DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"

DEMO_USER = {
    "user_id": "demo-user-001",
    "email": "demo@openglaze.local",
    "tier": "studio",
}


class AuthMiddleware:
    """
    Flask middleware for authentication.

    Security features:
    - Bearer token extraction from Authorization header
    - Session cookie validation
    - Request timing for security logging
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize middleware with Flask app."""
        app.before_request(self._before_request)

    def _before_request(self):
        """Process request before routing."""
        # Store request start time for timing
        g._auth_start_time = None  # Set by timing middleware

        # Skip auth for health checks and public endpoints
        if request.path in ("/health", "/api/mode", "/api/health"):
            g.current_user = None
            return

        # Check if auth is enabled
        if not getattr(self.app.config.get("MODE"), "AUTH_ENABLED", False):
            g.current_user = None
            return

        # Try to authenticate
        self._authenticate_request()

    def _authenticate_request(self):
        """Authenticate the current request."""
        from .kratos_client import (
            get_kratos_client,
            AuthenticationError,
            SessionExpiredError,
        )

        # Try Bearer token first
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if token:
                try:
                    kratos = get_kratos_client()
                    session = kratos.validate_session(token)
                    g.current_user = {
                        "user_id": session.user_id,
                        "email": session.email,
                        "role": "user",
                        "session_id": session.session_id,
                    }
                    logger.debug(f"Authenticated user: {session.email}")
                    return
                except AuthenticationError as e:
                    logger.warning(f"Authentication failed: {e}")
                    g.current_user = None
                    g.auth_error = str(e)
                except SessionExpiredError as e:
                    logger.info(f"Session expired: {e}")
                    g.current_user = None
                    g.auth_error = str(e)
                except Exception as e:
                    logger.error(f"Auth error: {e}")
                    g.current_user = None
                    g.auth_error = "Authentication service unavailable"

        # Try session cookie
        session_token = request.cookies.get("ory_kratos_session")
        if session_token:
            try:
                kratos = get_kratos_client()
                session = kratos.validate_session(session_token)
                g.current_user = {
                    "user_id": session.user_id,
                    "email": session.email,
                    "role": "user",
                    "session_id": session.session_id,
                }
                logger.debug(f"Authenticated user via cookie: {session.email}")
                return
            except Exception as e:
                logger.debug(f"Cookie auth failed: {e}")

        # No valid authentication found
        g.current_user = None
        g.auth_error = None


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for an endpoint.

    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_endpoint():
            user = get_current_user()
            return jsonify({"user": user['email']})
    """

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, "current_user"):
            return (
                jsonify({"error": "Authentication required", "code": "AUTH_REQUIRED"}),
                401,
            )

        if g.current_user is None:
            # Demo mode fallback
            if DEMO_MODE:
                g.current_user = DEMO_USER
                return f(*args, **kwargs)
            error_msg = getattr(
                g, "auth_error", "Please log in to access this resource"
            )
            return (
                jsonify(
                    {
                        "error": "Authentication required",
                        "message": error_msg,
                        "code": "AUTH_REQUIRED",
                    }
                ),
                401,
            )

        return f(*args, **kwargs)

    return decorated_function


def get_current_user() -> Optional[dict]:
    """
    Get the currently authenticated user.
    Falls back to DEMO_USER when DEMO_MODE is enabled.
    """
    user = getattr(g, "current_user", None)
    if user is None and DEMO_MODE:
        return DEMO_USER
    return user


def get_user_id() -> Optional[str]:
    """Get the current user's ID or None."""
    user = get_current_user()
    return user.get("user_id") if user else None


def optional_auth(f: Callable) -> Callable:
    """
    Decorator that allows but doesn't require authentication.
    Sets g.current_user if authenticated, None otherwise.
    """

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Auth middleware already sets g.current_user
        return f(*args, **kwargs)

    return decorated_function


def get_user_id_or_simple() -> Optional[str]:
    """
    Get user_id from Ory Kratos session or simple auth token.
    Checks Bearer token header — if it matches a simple auth session,
    returns that user_id. Otherwise falls back to Ory Kratos.
    """
    # Check simple auth first (Bearer token)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            try:
                from .simple_auth import validate_session

                session = validate_session(token)
                if session:
                    return session["user_id"]
            except Exception:
                pass

    # Fall back to Ory Kratos
    return get_user_id()


def get_simple_user() -> Optional[dict]:
    """
    Get simple auth user info if authenticated via simple auth.
    Returns {user_id, display_name} or None.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            try:
                from .simple_auth import validate_session

                return validate_session(token)
            except Exception:
                pass
    return None
