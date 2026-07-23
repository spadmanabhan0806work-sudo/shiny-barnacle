from __future__ import annotations

import base64
import json
from enum import Enum
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.infrastructure.config.settings import get_settings


class Role(str, Enum):
    ANNOTATOR = "annotator"
    REVIEWER = "reviewer"
    ADMIN = "admin"


ROLE_HIERARCHY = {
    Role.ANNOTATOR: 1,
    Role.REVIEWER: 2,
    Role.ADMIN: 3,
}

# path prefix -> minimum role required
ROUTE_PERMISSIONS: dict[str, Role] = {
    "/api/v1/annotations": Role.ANNOTATOR,
    "/api/v1/calls": Role.ANNOTATOR,
    "/api/v1/reviews": Role.REVIEWER,
    "/api/v1/prompts": Role.ADMIN,
    "/api/v1/evaluations": Role.ADMIN,
    "/api/v1/exports": Role.REVIEWER,
    "/api/v1/analytics": Role.REVIEWER,
}

PUBLIC_PATHS = {"/api/v1/health", "/api/v1/ready", "/docs", "/openapi.json", "/redoc"}


def _decode_stub_token(token: str) -> dict | None:
    """Decode a base64-encoded JSON stub token for dev/test OIDC."""
    try:
        payload = json.loads(base64.urlsafe_b64decode(token + "=="))
        return payload
    except (json.JSONDecodeError, ValueError):
        return None


def _role_from_claims(claims: dict) -> Role:
    roles = claims.get("roles") or claims.get("realm_access", {}).get("roles", [])
    if isinstance(roles, str):
        roles = [roles]
    if "admin" in roles:
        return Role.ADMIN
    if "reviewer" in roles:
        return Role.REVIEWER
    if "annotator" in roles:
        return Role.ANNOTATOR
    return Role(claims.get("role", Role.ANNOTATOR.value))


def _required_role(path: str) -> Role | None:
    for prefix, role in ROUTE_PERMISSIONS.items():
        if path.startswith(prefix):
            return role
    return None


class AuthUser:
    def __init__(self, user_id: str, role: Role) -> None:
        self.user_id = user_id
        self.role = role

    def has_role(self, required: Role) -> bool:
        return ROLE_HIERARCHY[self.role] >= ROLE_HIERARCHY[required]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        auth_config = settings.get("auth", {})
        enabled = auth_config.get("enabled", False)

        if not enabled or request.url.path in PUBLIC_PATHS:
            request.state.user = AuthUser("anonymous", Role.ADMIN)
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing bearer token"})

        token = auth_header[7:]
        claims = _decode_stub_token(token)
        if claims is None:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        user = AuthUser(
            user_id=claims.get("sub", "unknown"),
            role=_role_from_claims(claims),
        )
        request.state.user = user

        required = _required_role(request.url.path)
        if required and not user.has_role(required):
            return JSONResponse(status_code=403, content={"detail": "Insufficient permissions"})

        return await call_next(request)
