"""Authentication API endpoints for OIDC information, user profile, and demo mode."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.core.config import settings
from app.core.security import get_current_user, is_localhost_ip, ROLE_HIERARCHY
from app.models.schemas import UserIdentity, DemoLoginRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=UserIdentity)
def get_profile(current_user: UserIdentity = Depends(get_current_user)) -> UserIdentity:
    """Returns the profile of the currently authenticated user."""
    return current_user


@router.get("/config")
def get_auth_config() -> Dict[str, Any]:
    """Provides client-side OIDC configuration parameters and demo mode state."""
    return {
        "oidc_issuer_url": settings.oidc_issuer_url,
        "oidc_client_id": settings.oidc_client_id,
        "oidc_redirect_uri": settings.oidc_redirect_uri,
        "oidc_audience": settings.oidc_audience,
        "demo_mode_enabled": settings.demo_mode and settings.environment != "production",
        "environment": settings.environment,
    }


@router.post("/demo-login", response_model=UserIdentity)
def demo_login(req: DemoLoginRequest, request: Request) -> UserIdentity:
    """
    Simulates role-based login for local testing.
    Strictly restricted to localhost loopback and non-production environments.
    """
    if not settings.demo_mode or settings.environment == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login is disabled in this environment.",
        )

    client_host = request.client.host if request.client else "127.0.0.1"
    if not is_localhost_ip(client_host):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login is only accessible from local loopback address.",
        )

    role = req.role.strip().lower()
    if role not in ROLE_HIERARCHY:
        role = "operator"

    username = req.username or f"demo-{role}"
    return UserIdentity(
        username=username,
        email=f"{username}@example.local",
        role=role,
        is_authenticated=True,
        auth_source="demo",
    )


@router.post("/logout")
def logout() -> Dict[str, str]:
    """Explicit logout endpoint for client session cleanup."""
    return {"status": "logged_out", "message": "Session invalidated."}
