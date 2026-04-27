"""
OpenGlaze Security Middleware
Rate limiting, security headers, and request validation.
"""

import os
import time
import hashlib
import logging
import threading
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class RateLimitEntry:
    """Rate limit tracking entry."""

    count: int = 0
    window_start: float = 0.0
    blocked_until: float = 0.0


class InMemoryRateLimiter:
    """
    Thread-safe in-memory rate limiter.

    Implements sliding window rate limiting with:
    - Per-IP tracking
    - Per-endpoint limits
    - Automatic cleanup
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        block_duration_minutes: int = 5,
        cleanup_interval: int = 300,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.block_duration = block_duration_minutes * 60
        self.cleanup_interval = cleanup_interval

        self._entries: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._lock = threading.RLock()
        self._last_cleanup = time.time()

    def _get_key(self, identifier: str, endpoint: str = None) -> str:
        """Generate rate limit key."""
        if endpoint:
            return hashlib.sha256(f"{identifier}:{endpoint}".encode()).hexdigest()[:32]
        return hashlib.sha256(identifier.encode()).hexdigest()[:32]

    def _cleanup_if_needed(self) -> None:
        """Remove old entries periodically."""
        if time.time() - self._last_cleanup > self.cleanup_interval:
            with self._lock:
                now = time.time()
                old_keys = [
                    k
                    for k, v in self._entries.items()
                    if now - v.window_start > 7200  # 2 hours
                ]
                for key in old_keys:
                    del self._entries[key]
                if old_keys:
                    logger.debug(f"Cleaned up {len(old_keys)} rate limit entries")
                self._last_cleanup = now

    def check_rate_limit(
        self, identifier: str, endpoint: str = None
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request should be rate limited.

        Args:
            identifier: Client identifier (IP, user ID, etc.)
            endpoint: Optional endpoint-specific limit

        Returns:
            Tuple of (allowed: bool, info: dict)
            info contains: remaining, reset_at, retry_after
        """
        self._cleanup_if_needed()
        key = self._get_key(identifier, endpoint)
        now = time.time()

        with self._lock:
            entry = self._entries[key]

            # Check if currently blocked
            if entry.blocked_until > now:
                return False, {
                    "remaining": 0,
                    "reset_at": entry.blocked_until,
                    "retry_after": int(entry.blocked_until - now),
                }

            # Reset window if expired
            if now - entry.window_start > 60:
                entry.count = 0
                entry.window_start = now

            # Check limit
            if entry.count >= self.requests_per_minute:
                # Block for remaining time
                entry.blocked_until = now + self.block_duration
                return False, {
                    "remaining": 0,
                    "reset_at": entry.blocked_until,
                    "retry_after": self.block_duration,
                }

            # Increment and allow
            entry.count += 1
            remaining = self.requests_per_minute - entry.count
            reset_at = entry.window_start + 60

            return True, {
                "remaining": remaining,
                "reset_at": reset_at,
                "retry_after": 0,
            }

    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        with self._lock:
            return {
                "total_tracked": len(self._entries),
                "currently_blocked": sum(
                    1 for e in self._entries.values() if e.blocked_until > time.time()
                ),
            }


def get_client_identifier() -> str:
    """Get client identifier from request.

    Only trusts proxy headers when TRUSTED_PROXY is configured via
    environment variable.  Without that setting, only the direct
    remote_addr is used to prevent header spoofing.
    """
    import os
    from flask import request

    trusted_proxy = os.environ.get("TRUSTED_PROXY", "")
    if trusted_proxy and request.remote_addr == trusted_proxy:
        # Behind a known reverse proxy — trust the first value
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

    # Direct connection or untrusted proxy
    return request.remote_addr or "unknown"


def rate_limit(requests_per_minute: int = None, key_func: callable = None):
    """
    Flask decorator for rate limiting.

    Usage:
        @app.route('/api/ask')
        @rate_limit(requests_per_minute=10)
        def ask_ai():
            ...
    """
    from flask import request, g, jsonify

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get rate limiter from app config
            limiter = getattr(g, "rate_limiter", None) or getattr(
                request.app.extensions.get("rate_limiter"), "limiter", None
            )

            if limiter is None:
                # No rate limiter configured, allow
                return f(*args, **kwargs)

            # Get client identifier
            identifier = (key_func or get_client_identifier)()

            # Check rate limit
            allowed, info = limiter.check_rate_limit(identifier)

            if not allowed:
                response = jsonify(
                    {
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Try again in {info['retry_after']} seconds.",
                        "retry_after": info["retry_after"],
                        "code": "RATE_LIMITED",
                    }
                )
                response.status_code = 429
                response.headers["Retry-After"] = str(info["retry_after"])
                return response

            from flask import Response as FlaskResponse

            response = f(*args, **kwargs)
            # Handle tuple returns like (response, status_code)
            if isinstance(response, tuple):
                resp_obj = response[0]
                if not isinstance(resp_obj, FlaskResponse):
                    resp_obj = jsonify(resp_obj)
                if len(response) > 1 and hasattr(resp_obj, "status_code"):
                    resp_obj.status_code = response[1]
                response = resp_obj
            elif not isinstance(response, FlaskResponse):
                response = jsonify(response)
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(int(info["reset_at"]))
            return response

        return decorated_function

    return decorator


class SecurityHeaders:
    """
    Security headers middleware.

    Adds security headers to all responses:
    - Content-Security-Policy
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with Flask app."""
        app.after_request(self._add_security_headers)

    def _add_security_headers(self, response):
        """Add security headers to response."""

        # Content Security Policy.
        # Script-src keeps 'unsafe-inline' because the SPA still uses inline
        # onclick handlers in index.html (sidebar, modal, family filters).
        # TODO: Migrate all inline handlers to addEventListener, then remove
        # 'unsafe-inline' and use nonce-based CSP instead.
        csp_script_nonce = getattr(response, "_csp_script_nonce", "")
        script_src = (
            f"'self' 'unsafe-inline' 'nonce-{csp_script_nonce}' https://cdn.jsdelivr.net"
            if csp_script_nonce
            else "'self' 'unsafe-inline' https://cdn.jsdelivr.net"
        )
        csp = (
            f"default-src 'self'; "
            f"script-src {script_src}; "
            f"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            f"font-src 'self' https://fonts.gstatic.com; "
            f"img-src 'self' data: blob: https:; "
            f"connect-src 'self' http://localhost:* ws://localhost:*; "
            f"frame-ancestors 'none'; "
            f"base-uri 'self'; "
            f"form-action 'self';"
        )
        response.headers["Content-Security-Policy"] = csp

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        return response


class HTTPSRedirect:
    """
    HTTPS redirection middleware for production.
    """

    def __init__(self, app=None, hsts_max_age: int = 31536000):
        self.hsts_max_age = hsts_max_age
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with Flask app."""
        # Only enable in production
        if os.environ.get("HTTPS_ENFORCE", "false").lower() == "true":
            app.before_request(self._redirect_to_https)
            app.after_request(self._add_hsts_header)

    def _redirect_to_https(self):
        """Redirect HTTP to HTTPS."""
        from flask import request, redirect

        if not request.is_secure:
            url = request.url.replace("http://", "https://", 1)
            return redirect(url, code=301)

    def _add_hsts_header(self, response):
        """Add HSTS header."""
        response.headers["Strict-Transport-Security"] = (
            f"max-age={self.hsts_max_age}; includeSubDomains; preload"
        )
        return response


# Global rate limiter instance
_rate_limiter: Optional[InMemoryRateLimiter] = None


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get or create rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        rpm = int(os.environ.get("RATELIMIT_PER_MINUTE", "60"))
        _rate_limiter = InMemoryRateLimiter(requests_per_minute=rpm)
    return _rate_limiter


def init_security(app) -> None:
    """Initialize all security middleware."""
    from flask import g

    # Security headers
    SecurityHeaders(app)

    # HTTPS redirect (if enabled)
    HTTPSRedirect(app)

    # Rate limiter
    limiter = get_rate_limiter()
    app.extensions["rate_limiter"] = {"limiter": limiter}

    @app.before_request
    def set_rate_limiter():
        g.rate_limiter = limiter

    logger.info("Security middleware initialized")
