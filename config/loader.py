"""
OpenGlaze Configuration Loader
Detects runtime mode (personal vs cloud) and provides appropriate configuration.
Security-hardened as of March 2026.
"""

import os
import re
import yaml
import secrets
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required values."""

    pass


@dataclass
class SecurityConfig:
    """Security-related configuration."""

    rate_limiting_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_storage_url: str = "memory://"
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:8767"])
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: str = "Lax"
    https_enforce: bool = False
    hsts_max_age: int = 31536000
    secret_key: str = ""


@dataclass
class ModeConfig:
    """Base configuration for any mode."""

    AUTH_ENABLED: bool = False
    MULTI_TENANT: bool = False
    API_ACCESS: bool = False
    ANALYTICS: bool = False
    DEFAULT_THEME: str = "dark"
    DB_TYPE: str = "sqlite"
    DB_PATH: str = "glaze.db"
    DEBUG: bool = False
    HOST: str = "127.0.0.1"
    PORT: int = 8767
    security: SecurityConfig = field(default_factory=SecurityConfig)

    def __post_init__(self):
        self.name = "base"


@dataclass
class PersonalMode(ModeConfig):
    """Personal mode: Single-user, local SQLite, no auth/billing."""

    def __post_init__(self):
        self.name = "personal"
        self.AUTH_ENABLED = False
        self.MULTI_TENANT = False
        self.API_ACCESS = False
        self.ANALYTICS = False
        self.DEFAULT_THEME = "dark"
        self.DB_TYPE = "sqlite"
        self.DB_PATH = os.environ.get("DATABASE_PATH", "glaze.db")
        self.DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
        self.HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
        self.PORT = int(os.environ.get("FLASK_PORT", "8767"))

        # Security defaults for personal mode
        self.security = SecurityConfig(
            rate_limiting_enabled=True,
            rate_limit_per_minute=int(os.environ.get("RATELIMIT_PER_MINUTE", "60")),
            cookie_secure=False,  # Personal mode typically runs locally
            https_enforce=False,
            secret_key=self._get_or_create_secret_key(),
        )

    def _get_or_create_secret_key(self) -> str:
        """Get secret key from environment or generate one for this session."""
        key = os.environ.get("SECRET_KEY")
        if not key:
            # Generate a random key for this session (won't persist across restarts)
            key = secrets.token_hex(32)
            logger.info(
                "Generated session secret key (set SECRET_KEY env var for persistence)"
            )
        return key


@dataclass
class CloudMode(ModeConfig):
    """Cloud mode: Multi-tenant, PostgreSQL, auth via Ory Kratos."""

    # Tier levels
    TIER_FREE: str = "free"
    TIER_PRO: str = "pro"
    TIER_STUDIO: str = "studio"

    def __post_init__(self):
        self.name = "cloud"
        self.AUTH_ENABLED = True
        self.MULTI_TENANT = True
        self.API_ACCESS = True
        self.ANALYTICS = True
        self.DEFAULT_THEME = "light"
        self.DB_TYPE = "postgresql"
        self.DEBUG = False  # NEVER enable debug in cloud mode

        self.HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
        self.PORT = int(os.environ.get("FLASK_PORT", "8080"))

        # Validate required environment variables
        self._validate_required_env_vars()

        # Security settings for cloud mode
        self.security = SecurityConfig(
            rate_limiting_enabled=True,
            rate_limit_per_minute=int(os.environ.get("RATELIMIT_PER_MINUTE", "60")),
            rate_limit_storage_url=os.environ.get(
                "RATELIMIT_STORAGE_URL", "redis://localhost:6379"
            ),
            cors_origins=self._parse_cors_origins(),
            cookie_secure=os.environ.get("SESSION_COOKIE_SECURE", "true").lower()
            == "true",
            cookie_httponly=True,
            cookie_samesite="Lax",
            https_enforce=os.environ.get("HTTPS_ENFORCE", "true").lower() == "true",
            secret_key=self._require_env("SECRET_KEY"),
        )

    def _validate_required_env_vars(self):
        """Validate that all required environment variables are set."""
        required = ["POSTGRES_HOST", "POSTGRES_PASSWORD", "SECRET_KEY"]
        missing = [v for v in required if not os.environ.get(v)]

        if missing:
            raise ConfigurationError(
                f"Missing required environment variables for cloud mode: {', '.join(missing)}. "
                "Set these before starting the application."
            )

    def _require_env(self, name: str) -> str:
        """Get required environment variable or raise error."""
        value = os.environ.get(name)
        if not value:
            raise ConfigurationError(f"Required environment variable {name} is not set")
        return value

    def _parse_cors_origins(self) -> List[str]:
        """Parse CORS origins from environment."""
        origins_str = os.environ.get("CORS_ORIGINS", "")
        if not origins_str:
            return []
        return [o.strip() for o in origins_str.split(",") if o.strip()]

    def get_tier_features(self, tier: str) -> dict:
        """Return feature flags for a specific tier."""
        base_features = {
            "glaze_crud": True,
            "combinations": True,
            "experiments": True,
            "kama_ai": True,
            "templates": True,
        }

        tier_features = {
            self.TIER_FREE: {
                "multi_user": False,
                "analytics": False,
                "api_access": False,
                "max_users": 1,
            },
            self.TIER_PRO: {
                "multi_user": True,
                "analytics": True,
                "api_access": True,
                "max_users": 2,
            },
            self.TIER_STUDIO: {
                "multi_user": True,
                "analytics": True,
                "api_access": True,
                "max_users": 10,
            },
        }

        features = base_features.copy()
        features.update(tier_features.get(tier, {}))
        return features


def detect_mode() -> ModeConfig:
    """
    Detect runtime mode based on environment and config.

    Priority:
    1. OPENGLAZE_MODE environment variable (personal/cloud)
    2. OPENGLAZE_CLOUD environment variable (legacy, if true = cloud)
    3. config file presence
    4. Default to personal mode

    Raises:
        ConfigurationError: If cloud mode is requested but required vars are missing
    """
    # Check explicit mode env var
    mode_env = os.environ.get("OPENGLAZE_MODE", "").lower()

    if mode_env == "cloud":
        logger.info("Cloud mode requested via OPENGLAZE_MODE environment variable")
        try:
            return CloudMode()
        except ConfigurationError as e:
            logger.error(f"Cloud mode configuration error: {e}")
            raise

    if mode_env == "personal":
        logger.info("Personal mode requested via OPENGLAZE_MODE environment variable")
        return PersonalMode()

    # Check legacy cloud flag
    if os.environ.get("OPENGLAZE_CLOUD", "").lower() in ("true", "1", "yes"):
        logger.info(
            "Cloud mode requested via OPENGLAZE_CLOUD environment variable (legacy)"
        )
        try:
            return CloudMode()
        except ConfigurationError as e:
            logger.error(f"Cloud mode configuration error: {e}")
            raise

    # Check for cloud config file presence (indicates cloud deployment)
    config_dir = Path(__file__).parent
    cloud_config = config_dir / "cloud.yaml"
    if cloud_config.exists():
        # Check if required cloud env vars are set
        if os.environ.get("POSTGRES_HOST") and os.environ.get("POSTGRES_PASSWORD"):
            logger.info("Cloud mode detected via config file and environment")
            try:
                return CloudMode()
            except ConfigurationError as e:
                logger.warning(f"Cloud config present but configuration error: {e}")
                logger.info("Falling back to personal mode")
                return PersonalMode()

    # Default to personal mode
    logger.info("Using personal mode (default)")
    return PersonalMode()


def load_config(mode: Optional[ModeConfig] = None) -> dict:
    """
    Load configuration from YAML file based on mode.

    Args:
        mode: ModeConfig instance. If None, auto-detects.

    Returns:
        Dictionary with configuration values.
    """
    if mode is None:
        mode = detect_mode()

    config_dir = Path(__file__).parent
    config_file = config_dir / f"{mode.name}.yaml"

    config = {}

    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                raw_content = f.read()

            # Substitute environment variables
            content = _substitute_env_vars(raw_content)

            config = yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            logger.warning(f"Error loading config file {config_file}: {e}")

    # Add mode info
    config["mode"] = mode

    return config


def _substitute_env_vars(content: str) -> str:
    """
    Substitute environment variables in YAML content.
    Supports ${VAR_NAME} and ${VAR_NAME:default} syntax.

    Security: Only allows specific patterns to prevent injection.
    """
    # Pattern: ${VAR_NAME} or ${VAR_NAME:default}
    pattern = r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}"

    def replacer(match):
        var_name = match.group(1)
        default = match.group(2)

        # Only allow specific characters in default values
        if default and not re.match(r"^[a-zA-Z0-9_:/\.\-\+]*$", default):
            logger.warning(f"Invalid default value for {var_name}, using empty string")
            default = ""

        value = os.environ.get(var_name, default if default is not None else "")

        # For sensitive values, don't log the actual value
        if any(
            sensitive in var_name.upper()
            for sensitive in ["PASSWORD", "SECRET", "KEY", "TOKEN", "CREDENTIAL"]
        ):
            log_value = "***REDACTED***"
        else:
            log_value = value[:50] + "..." if len(value) > 50 else value

        logger.debug(f"Substituted ${{{var_name}}} -> {log_value}")
        return value

    return re.sub(pattern, replacer, content)


# Convenience exports
__all__ = [
    "detect_mode",
    "load_config",
    "PersonalMode",
    "CloudMode",
    "ModeConfig",
    "SecurityConfig",
    "ConfigurationError",
]
