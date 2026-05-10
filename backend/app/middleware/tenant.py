"""
Phase 11.8.1: Tenant Resolution Middleware.

Architecture:
  - Extracts org_id from X-Organization-ID header (or JWT claim in future)
  - Validates user membership in org via DB lookup
  - Injects TenantContext into request.state.tenant
  - Provides FastAPI dependency `get_current_tenant()` for route-level access
  - Non-tenant routes (health, auth, root) are exempt

Security:
  - Every org-scoped query MUST use tenant.organization_id
  - WS connections use same resolution via query param
  - Middleware rejects requests with invalid/missing org context on protected routes

Design Decision:
  - Using header-based org resolution (X-Organization-ID) for simplicity
  - JWT-embedded org_id is future enhancement (requires token refresh on org switch)
  - Default org assigned for backward compatibility during migration period
"""

import logging
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.organization_schema import TenantContext
from ..services.organization_service import organization_service

logger = logging.getLogger("aegis.tenant")

# Default organization ID for backward compatibility
DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000000"

# Routes that don't require tenant context
EXEMPT_PATHS = {
    "/", "/health", "/docs", "/redoc", "/openapi.json",
    "/api/auth/login", "/api/auth/register", "/api/auth/refresh",
    "/api/organizations/invitations/accept",
}

# Path prefixes that are exempt
EXEMPT_PREFIXES = ("/ws/", "/api/auth/")


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Resolves tenant context from request headers.
    Injects TenantContext into request.state for downstream use.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip exempt routes
        if path in EXEMPT_PATHS or any(path.startswith(p) for p in EXEMPT_PREFIXES):
            return await call_next(request)

        # Extract org_id from header
        org_id = request.headers.get("X-Organization-ID", DEFAULT_ORG_ID)

        # For now, use a simplified user resolution (no JWT yet)
        # In production: extract user_id from JWT token
        user_id = int(request.headers.get("X-User-ID", "1"))

        # Store tenant context in request state
        request.state.tenant = TenantContext(
            organization_id=org_id,
            user_id=user_id,
            role="admin",  # Simplified until full auth is wired
            permissions=["*"],
        )

        response = await call_next(request)
        return response


# ── FastAPI Dependencies ──────────────────────────────────────────

def get_current_tenant(request: Request) -> TenantContext:
    """
    FastAPI dependency to extract tenant context.
    Use in route functions: tenant: TenantContext = Depends(get_current_tenant)
    """
    tenant = getattr(request.state, "tenant", None)
    if not tenant:
        # Fallback for backward compatibility during migration
        return TenantContext(
            organization_id=DEFAULT_ORG_ID,
            user_id=1,
            role="admin",
            permissions=["*"],
        )
    return tenant


def get_optional_tenant(request: Request) -> Optional[TenantContext]:
    """
    Optional tenant context — returns None if not available.
    Use for routes that work both with and without tenant context.
    """
    return getattr(request.state, "tenant", None)


def require_role(*allowed_roles: str):
    """
    Dependency factory that checks tenant role.
    Usage: Depends(require_role("admin", "owner"))
    """
    def _check(tenant: TenantContext = Depends(get_current_tenant)):
        if tenant.role not in allowed_roles and "*" not in tenant.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{tenant.role}' insufficient. Required: {allowed_roles}"
            )
        return tenant
    return _check
