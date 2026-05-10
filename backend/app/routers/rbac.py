"""
Phase 11.8.2: Advanced RBAC API Routes.

Endpoints:
  GET    /api/organizations/{org_id}/permissions/me    — Get current user's resolved permissions
  GET    /api/organizations/{org_id}/roles             — List available roles (system + org custom)
  POST   /api/organizations/{org_id}/roles             — Create custom role
  POST   /api/organizations/{org_id}/members/{user_id}/roles — Assign roles to member
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..middleware.tenant import get_current_tenant, require_permissions
from ..schemas.organization_schema import TenantContext
from ..schemas.rbac_schema import RoleResponse, RoleCreate, MemberRoleAssign, PermissionResponse
from ..services.advanced_rbac_service import rbac_service
from ..models.rbac import Permission

router = APIRouter(prefix="/api/organizations/{org_id}", tags=["rbac"])

@router.get("/permissions/me", response_model=List[str])
def get_my_permissions(
    org_id: str,
    tenant: TenantContext = Depends(get_current_tenant),
):
    """Get resolved permissions for the current user in this org."""
    if org_id != tenant.organization_id:
        raise HTTPException(status_code=403, detail="Cross-tenant request denied")
    return tenant.permissions


@router.get("/permissions", response_model=List[PermissionResponse])
def get_system_permissions(
    org_id: str,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_permissions("org:manage"))
):
    """List all available system permissions."""
    return db.query(Permission).all()


@router.get("/roles", response_model=List[RoleResponse])
def list_roles(
    org_id: str,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_permissions("member:manage")),
):
    """List available roles (system defaults + org custom)."""
    return rbac_service.get_org_roles(db, org_id)


@router.post("/roles", response_model=RoleResponse, status_code=201)
def create_role(
    org_id: str,
    data: RoleCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_permissions("org:manage")),
):
    """Create a custom role for the organization."""
    try:
        return rbac_service.create_custom_role(db, org_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/members/{user_id}/roles", status_code=204)
def assign_member_roles(
    org_id: str,
    user_id: int,
    data: MemberRoleAssign,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(require_permissions("member:manage")),
):
    """Assign specific roles to an organization member, replacing existing."""
    try:
        rbac_service.assign_roles_to_member(db, org_id, user_id, data.role_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
