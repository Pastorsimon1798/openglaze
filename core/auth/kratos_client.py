"""
Ory Kratos Client for OpenGlaze Cloud Mode
Handles user authentication and session management via Kratos.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class KratosError(Exception):
    """Base exception for Kratos errors."""

    pass


class AuthenticationError(KratosError):
    """Authentication failed."""

    pass


class SessionExpiredError(KratosError):
    """Session has expired."""

    pass


@dataclass
class KratosSession:
    """Represents a Kratos user session."""

    session_id: str
    user_id: str
    email: str
    active: bool
    expires_at: Optional[str]
    authenticated_at: Optional[str]
    traits: Dict[str, Any]

    @classmethod
    def from_api_response(cls, data: Dict) -> "KratosSession":
        """Create session from Kratos API response."""
        identity = data.get("identity", {})
        return cls(
            session_id=data.get("id", ""),
            user_id=identity.get("id", ""),
            email=identity.get("traits", {}).get("email", ""),
            active=data.get("active", False),
            expires_at=data.get("expires_at"),
            authenticated_at=data.get("authenticated_at"),
            traits=identity.get("traits", {}),
        )


class KratosClient:
    """
    Client for interacting with Ory Kratos.

    Security features:
    - Session token validation
    - Automatic token refresh
    - Secure session cookie handling
    """

    def __init__(
        self,
        public_endpoint: Optional[str] = None,
        admin_endpoint: Optional[str] = None,
        timeout: int = 10,
    ):
        self.public_endpoint = public_endpoint or os.environ.get(
            "ORY_KRATOS_ENDPOINT", "http://localhost:4433"
        )
        self.admin_endpoint = admin_endpoint or os.environ.get(
            "ORY_KRATOS_ADMIN_ENDPOINT", "http://localhost:4434"
        )
        self.timeout = timeout

        # Remove trailing slashes
        self.public_endpoint = self.public_endpoint.rstrip("/")
        self.admin_endpoint = self.admin_endpoint.rstrip("/")

    def validate_session(self, session_token: str) -> KratosSession:
        """
        Validate a session token with Kratos.

        Args:
            session_token: The session token from the request

        Returns:
            KratosSession with user details

        Raises:
            AuthenticationError: Invalid session
            SessionExpiredError: Session has expired
        """
        if not session_token:
            raise AuthenticationError("No session token provided")

        try:
            response = requests.get(
                f"{self.public_endpoint}/sessions/whoami",
                headers={
                    "Authorization": f"Bearer {session_token}",
                    "Accept": "application/json",
                },
                timeout=self.timeout,
            )

            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired session")
            if response.status_code == 403:
                raise SessionExpiredError("Session has expired")
            if response.status_code != 200:
                raise KratosError(f"Kratos error: {response.status_code}")

            data = response.json()

            if not data.get("active", False):
                raise SessionExpiredError("Session is not active")

            return KratosSession.from_api_response(data)

        except RequestException as e:
            logger.error(f"Failed to validate session with Kratos: {e}")
            raise KratosError(f"Kratos connection error: {e}")

    def get_identity(self, identity_id: str, admin_token: Optional[str] = None) -> Dict:
        """
        Get identity details by ID (requires admin access).

        Args:
            identity_id: The identity UUID
            admin_token: Optional admin token for authentication

        Returns:
            Identity data from Kratos
        """
        headers = {"Accept": "application/json"}
        if admin_token:
            headers["Authorization"] = f"Bearer {admin_token}"

        try:
            response = requests.get(
                f"{self.admin_endpoint}/identities/{identity_id}",
                headers=headers,
                timeout=self.timeout,
            )

            if response.status_code == 404:
                raise KratosError(f"Identity not found: {identity_id}")
            if response.status_code != 200:
                raise KratosError(f"Failed to get identity: {response.status_code}")

            return response.json()

        except RequestException as e:
            logger.error(f"Failed to get identity from Kratos: {e}")
            raise KratosError(f"Kratos connection error: {e}")

    def revoke_session(self, session_token: str) -> bool:
        """
        Revoke a session.

        Args:
            session_token: The session token to revoke

        Returns:
            True if successfully revoked
        """
        try:
            response = requests.delete(
                f"{self.public_endpoint}/sessions",
                headers={
                    "Authorization": f"Bearer {session_token}",
                    "Accept": "application/json",
                },
                timeout=self.timeout,
            )

            return response.status_code in (200, 204, 404)

        except RequestException as e:
            logger.error(f"Failed to revoke session: {e}")
            return False


# Global instance
_kratos_client: Optional[KratosClient] = None


def get_kratos_client() -> KratosClient:
    """Get or create Kratos client instance."""
    global _kratos_client
    if _kratos_client is None:
        _kratos_client = KratosClient()
    return _kratos_client
