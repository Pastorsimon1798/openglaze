"""
Ory Kratos Authentication Integration
"""

import os
import requests
from functools import wraps
from flask import request, jsonify

ORY_KRATOS_PUBLIC = os.environ.get("KRATOS_PUBLIC_URL", "http://localhost:4433")
ORY_KRATOS_ADMIN = os.environ.get("KRATOS_ADMIN_URL", "http://localhost:4434")


def get_current_user(req):
    """Get user from Kratos session cookie.

    Args:
        req: Flask request object

    Returns:
        dict: User identity or None if not authenticated
    """
    session_cookie = req.cookies.get("ory_kratos_session")

    if not session_cookie:
        return None

    try:
        # Validate session with Kratos
        resp = requests.get(
            f"{ORY_KRATOS_PUBLIC}/sessions/whoami",
            cookies={"ory_kratos_session": session_cookie},
            timeout=5,
        )

        if resp.status_code != 200:
            return None

        session_data = resp.json()
        return session_data.get("identity")

    except requests.RequestException:
        return None


def get_user_by_id(user_id):
    """Get user identity by ID via admin API.

    Args:
        user_id: Kratos identity ID

    Returns:
        dict: User identity or None if not found
    """
    try:
        resp = requests.get(f"{ORY_KRATOS_ADMIN}/admin/identities/{user_id}", timeout=5)

        if resp.status_code != 200:
            return None

        return resp.json()

    except requests.RequestException:
        return None


def update_user_traits(user_id, traits):
    """Update user traits via admin API.

    Args:
        user_id: Kratos identity ID
        traits: Dict of traits to update

    Returns:
        dict: Updated identity or None on failure
    """
    try:
        # First get current identity
        identity = get_user_by_id(user_id)
        if not identity:
            return None

        # Merge traits
        current_traits = identity.get("traits", {})
        current_traits.update(traits)

        # Update via admin API
        resp = requests.put(
            f"{ORY_KRATOS_ADMIN}/admin/identities/{user_id}",
            json={
                "schema_id": identity.get("schema_id", "default"),
                "traits": current_traits,
            },
            timeout=5,
        )

        if resp.status_code != 200:
            return None

        return resp.json()

    except requests.RequestException:
        return None


def require_auth(f):
    """Decorator to require authentication for a route.

    Adds request.user with the current user identity.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user(request)
        if not user:
            return jsonify({"error": "Unauthorized", "login_url": "/auth/login"}), 401
        request.user = user
        return f(*args, **kwargs)

    return decorated


def create_identity(email, password=None, traits=None):
    """Create a new identity via admin API.

    Args:
        email: User email
        password: Optional password (if using password method)
        traits: Additional traits

    Returns:
        dict: Created identity or None on failure
    """
    if traits is None:
        traits = {}

    traits["email"] = email

    identity_data = {"schema_id": "default", "traits": traits}

    try:
        resp = requests.post(
            f"{ORY_KRATOS_ADMIN}/admin/identities", json=identity_data, timeout=5
        )

        if resp.status_code != 201:
            return None

        return resp.json()

    except requests.RequestException:
        return None


def delete_identity(user_id):
    """Delete an identity via admin API.

    Args:
        user_id: Kratos identity ID

    Returns:
        bool: True if deleted, False on failure
    """
    try:
        resp = requests.delete(
            f"{ORY_KRATOS_ADMIN}/admin/identities/{user_id}", timeout=5
        )

        return resp.status_code == 204

    except requests.RequestException:
        return False
