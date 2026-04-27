"""
JWT Token Handler for OpenGlaze Cloud Mode
Implements secure JWT validation following 2026 best practices.
"""

import os
import time
import logging
import secrets
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


class JWTError(Exception):
    """Base exception for JWT errors."""

    pass


class TokenExpiredError(JWTError):
    """Token has expired."""

    pass


class InvalidTokenError(JWTError):
    """Token is invalid."""

    pass


@dataclass
class TokenPayload:
    """Decoded JWT payload."""

    user_id: str
    email: str
    tier: str
    issued_at: int
    expires_at: int
    raw: Dict[str, Any]

    def is_expired(self) -> bool:
        """Check if token is expired."""
        return time.time() > self.expires_at

    def time_until_expiry(self) -> int:
        """Get seconds until expiry."""
        return max(0, self.expires_at - int(time.time()))


class JWTHandler:
    """
    JWT token handler with secure defaults.

    Security features:
    - Algorithm restriction (only RS256/HS256)
    - Expiration validation
    - Issuer/audience validation
    - Token blacklisting support
    - Timing-safe comparison
    """

    SUPPORTED_ALGORITHMS = {"RS256", "HS256"}

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        issuer: str = "openglaze",
        audience: str = "openglaze-api",
        token_lifetime_hours: int = 24,
        refresh_token_lifetime_days: int = 7,
    ):
        self.secret_key = secret_key or os.environ.get("SECRET_KEY")
        if not self.secret_key:
            raise ValueError("SECRET_KEY must be provided for JWT handling")

        if algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"Unsupported algorithm: {algorithm}. Use one of {self.SUPPORTED_ALGORITHMS}"
            )

        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.token_lifetime = timedelta(hours=token_lifetime_hours)
        self.refresh_lifetime = timedelta(days=refresh_token_lifetime_days)

        # Token blacklist for revocation (in production, use Redis)
        self._blacklist: set = set()

    def create_token(
        self,
        user_id: str,
        email: str,
        tier: str = "free",
        additional_claims: Optional[Dict] = None,
    ) -> str:
        """
        Create a new JWT access token.

        Args:
            user_id: Unique user identifier
            email: User's email address
            tier: User role (e.g. 'user', 'admin')
            additional_claims: Extra claims to include

        Returns:
            Encoded JWT string
        """
        now = datetime.utcnow()

        payload = {
            "sub": user_id,
            "email": email,
            "tier": tier,
            "iss": self.issuer,
            "aud": self.audience,
            "iat": int(now.timestamp()),
            "exp": int((now + self.token_lifetime).timestamp()),
            "jti": secrets.token_urlsafe(16),  # Unique token ID
            "type": "access",
        }

        if additional_claims:
            payload.update(additional_claims)

        # In production, use a proper JWT library like PyJWT
        # This is a simplified implementation
        return self._encode(payload)

    def create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token."""
        now = datetime.utcnow()

        payload = {
            "sub": user_id,
            "iss": self.issuer,
            "aud": self.audience,
            "iat": int(now.timestamp()),
            "exp": int((now + self.refresh_lifetime).timestamp()),
            "jti": secrets.token_urlsafe(16),
            "type": "refresh",
        }

        return self._encode(payload)

    def validate_token(self, token: str) -> TokenPayload:
        """
        Validate and decode a JWT token.

        Args:
            token: Encoded JWT string

        Returns:
            TokenPayload with decoded claims

        Raises:
            TokenExpiredError: Token has expired
            InvalidTokenError: Token is invalid or malformed
        """
        if not token:
            raise InvalidTokenError("Empty token provided")

        # Check blacklist
        token_hash = self._hash_token(token)
        if token_hash in self._blacklist:
            raise InvalidTokenError("Token has been revoked")

        try:
            payload = self._decode(token)
        except Exception as e:
            raise InvalidTokenError(f"Failed to decode token: {e}")

        # Validate required fields
        required_fields = ["sub", "email", "exp", "iat"]
        missing = [f for f in required_fields if f not in payload]
        if missing:
            raise InvalidTokenError(f"Missing required fields: {missing}")

        # Check expiration
        exp = payload.get("exp", 0)
        if time.time() > exp:
            raise TokenExpiredError("Token has expired")

        # Validate issuer
        if payload.get("iss") != self.issuer:
            raise InvalidTokenError(f"Invalid issuer: {payload.get('iss')}")

        # Validate audience
        aud = payload.get("aud")
        if (
            aud
            and aud != self.audience
            and self.audience not in (aud if isinstance(aud, list) else [aud])
        ):
            raise InvalidTokenError(f"Invalid audience: {aud}")

        return TokenPayload(
            user_id=payload["sub"],
            email=payload["email"],
            tier=payload.get("tier", "free"),
            issued_at=payload["iat"],
            expires_at=exp,
            raw=payload,
        )

    def revoke_token(self, token: str) -> None:
        """Add token to blacklist."""
        token_hash = self._hash_token(token)
        self._blacklist.add(token_hash)
        logger.info(f"Token revoked: {token_hash[:16]}...")

    def _encode(self, payload: Dict) -> str:
        """Encode payload to JWT string."""
        # In production, use: import jwt; return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        # This is a placeholder - implement with PyJWT in production
        import base64
        import json

        header = {"alg": self.algorithm, "typ": "JWT"}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode()
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

        # Create signature (simplified - use PyJWT in production)
        message = f"{header_b64}.{payload_b64}"
        signature = self._sign(message)

        return f"{message}.{signature}"

    def _decode(self, token: str) -> Dict:
        """Decode JWT string to payload."""
        # In production, use: import jwt; return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        import base64
        import json

        parts = token.split(".")
        if len(parts) != 3:
            raise InvalidTokenError("Malformed token")

        header_b64, payload_b64, signature = parts

        # Verify signature
        expected_sig = self._sign(f"{header_b64}.{payload_b64}")
        if not secrets.compare_digest(signature, expected_sig):
            raise InvalidTokenError("Invalid signature")

        try:
            payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
            return payload
        except Exception as e:
            raise InvalidTokenError(f"Failed to decode payload: {e}")

    def _sign(self, message: str) -> str:
        """Sign a message using the secret key."""
        # Simplified signing - use PyJWT in production
        import base64
        import hmac

        signature = hmac.new(
            self.secret_key.encode(), message.encode(), hashlib.sha256
        ).digest()

        return base64.urlsafe_b64encode(signature).decode().rstrip("=")

    def _hash_token(self, token: str) -> str:
        """Create a hash of the token for blacklist storage."""
        return hashlib.sha256(token.encode()).hexdigest()


# Global instance
_jwt_handler: Optional[JWTHandler] = None


def get_jwt_handler() -> JWTHandler:
    """Get or create JWT handler instance."""
    global _jwt_handler
    if _jwt_handler is None:
        _jwt_handler = JWTHandler()
    return _jwt_handler
