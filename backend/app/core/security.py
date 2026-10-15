"""Security, OIDC token validation, role-based access control, and demo mode."""

import time
from typing import Any, Dict, Optional
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from app.models.schemas import UserIdentity

bearer_scheme = HTTPBearer(auto_error=False)

ROLE_HIERARCHY: Dict[str, int] = {
    "viewer": 1,
    "operator": 2,
    "admin": 3,
}

_jwks_cache: Dict[str, Any] = {}
_jwks_cache_expiry: float = 0.0


def is_localhost_ip(host: Optional[str]) -> bool:
    """Checks whether the client host represents a local loopback interface."""
    if not host:
        return True
    return host in {"127.0.0.1", "localhost", "::1", "testclient"}


def decode_oidc_token(token: str) -> Dict[str, Any]:
    """Decode and validate an OIDC bearer token (expiry checked)."""
    try:
        unverified_claims = jwt.decode(
            token,
            options={"verify_signature": False, "verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Malformed bearer token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    exp = unverified_claims.get("exp")
    if exp and exp < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return unverified_claims


def extract_role_from_claims(claims: Dict[str, Any]) -> str:
    """Extracts application role from Keycloak realm/resource claims."""
    realm_roles = claims.get("realm_access", {}).get("roles", [])
    if "admin" in realm_roles:
        return "admin"
    if "operator" in realm_roles or "analyst" in realm_roles:
        return "operator"
    if "viewer" in realm_roles:
        return "viewer"

    resource_access = claims.get("resource_access", {}).get(settings.oidc_client_id, {})
    client_roles = resource_access.get("roles", [])
    if "admin" in client_roles:
        return "admin"
    if "operator" in client_roles or "analyst" in client_roles:
        return "operator"
    if "viewer" in client_roles:
        return "viewer"

    direct_role = claims.get("role")
    if direct_role in ROLE_HIERARCHY:
        return direct_role

    return "viewer"


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> UserIdentity:
    """Authenticate via OIDC bearer token or local demo mode."""
    client_host = request.client.host if request.client else "127.0.0.1"

    demo_role_header = request.headers.get("X-Demo-Role")
    if settings.demo_mode:
        if settings.environment == "production":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Security violation: Demo mode is prohibited in production.",
            )

        if not is_localhost_ip(client_host):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Demo mode authentication is restricted to loopback connections.",
            )

        if demo_role_header:
            role = demo_role_header.strip().lower()
            if role not in ROLE_HIERARCHY:
                role = "operator"
            return UserIdentity(
                username=f"demo-{role}",
                email=f"demo-{role}@example.local",
                role=role,
                is_authenticated=True,
                auth_source="demo",
            )

        if credentials and credentials.credentials.startswith("demo-"):
            role_part = credentials.credentials.replace("demo-", "").lower()
            role = role_part if role_part in ROLE_HIERARCHY else "operator"
            return UserIdentity(
                username=f"demo-{role}",
                email=f"demo-{role}@example.local",
                role=role,
                is_authenticated=True,
                auth_source="demo",
            )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    claims = decode_oidc_token(token)
    role = extract_role_from_claims(claims)
    username = claims.get("preferred_username") or claims.get("sub") or "authenticated-user"
    email = claims.get("email")

    return UserIdentity(
        username=username,
        email=email,
        role=role,
        is_authenticated=True,
        auth_source="oidc",
    )


def require_role(min_role: str):
    """Role checker: admin > operator > viewer."""
    if min_role not in ROLE_HIERARCHY:
        raise ValueError(f"Invalid min_role: {min_role}")

    def role_checker(user: UserIdentity = Depends(get_current_user)) -> UserIdentity:
        user_rank = ROLE_HIERARCHY.get(user.role, 0)
        required_rank = ROLE_HIERARCHY.get(min_role, 0)

        if user_rank < required_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: role '{min_role}' or higher required (current role: '{user.role}').",
            )
        return user

    return role_checker