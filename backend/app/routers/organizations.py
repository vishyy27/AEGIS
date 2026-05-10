"""
Phase 11.8.1: Organization API Routes.

Endpoints:
  POST   /api/organizations/              — Create organization
  GET    /api/organizations/              — List user's organizations
  GET    /api/organizations/{org_id}      — Get organization details
  PATCH  /api/organizations/{org_id}      — Update organization
  GET    /api/organizations/{org_id}/members    — List members
  PATCH  /api/organizations/{org_id}/members/{user_id} — Update member role
  DELETE /api/organizations/{org_id}/members/{user_id} — Remove member
  POST   /api/organizations/{org_id}/invitations — Create invitation
  GET    /api/organizations/{org_id}/invitations  — List pending invitations
  POST   /api/organizations/invitations/accept   — Accept invitation
  DELETE /api/organizations/{org_id}/invitations/{inv_id} — Revoke invitation
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..middleware.tenant import get_current_tenant
from ..schemas.organization_schema import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationSummary, MemberResponse, MemberUpdate,
    InvitationCreate, InvitationResponse, InvitationAccept, TenantContext,
)
from ..services.organization_service import organization_service

logger = logging.getLogger("aegis.routes.organizations")

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


# ── Organization CRUD ─────────────────────────────────────────────

@router.post("/", response_model=OrganizationResponse, status_code=201)
def create_organization(
    data: OrganizationCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    try:
        return organization_service.create_organization(db, data, tenant.user_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=List[OrganizationSummary])
def list_user_organizations(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    return organization_service.get_user_organizations(db, tenant.user_id)


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    org = organization_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.patch("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    org = organization_service.update_organization(db, org_id, data)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


# ── Member Management ─────────────────────────────────────────────

@router.get("/{org_id}/members", response_model=List[MemberResponse])
def list_members(
    org_id: str,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    return organization_service.get_members(db, org_id)


@router.patch("/{org_id}/members/{user_id}", response_model=MemberResponse)
def update_member_role(
    org_id: str,
    user_id: int,
    data: MemberUpdate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    try:
        result = organization_service.update_member_role(
            db, org_id, user_id, data.role, tenant.role
        )
        if not result:
            raise HTTPException(status_code=404, detail="Member not found")
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{org_id}/members/{user_id}", status_code=204)
def remove_member(
    org_id: str,
    user_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    try:
        result = organization_service.remove_member(db, org_id, user_id)
        if not result:
            raise HTTPException(status_code=404, detail="Member not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Invitation Flow ───────────────────────────────────────────────

@router.post("/{org_id}/invitations", response_model=InvitationResponse, status_code=201)
def create_invitation(
    org_id: str,
    data: InvitationCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    try:
        return organization_service.create_invitation(db, org_id, data, tenant.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{org_id}/invitations", response_model=List[InvitationResponse])
def list_invitations(
    org_id: str,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    return organization_service.get_pending_invitations(db, org_id)


@router.post("/invitations/accept", response_model=MemberResponse)
def accept_invitation(
    data: InvitationAccept,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    try:
        result = organization_service.accept_invitation(db, data.token, tenant.user_id)
        if not result:
            raise HTTPException(status_code=404, detail="Invalid or expired invitation")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{org_id}/invitations/{invitation_id}", status_code=204)
def revoke_invitation(
    org_id: str,
    invitation_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
):
    result = organization_service.revoke_invitation(db, org_id, invitation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Invitation not found")
