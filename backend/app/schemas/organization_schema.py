"""
Phase 11.8.1: Organization Pydantic Schemas.

Contracts for organization CRUD, membership management, and invitation flow.
All responses use from_attributes for ORM compatibility.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Organization Schemas ──────────────────────────────────────────

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
    plan_tier: str = Field(default="free", pattern=r"^(free|team|enterprise)$")
    settings: Optional[Dict[str, Any]] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    settings: Optional[Dict[str, Any]] = None
    logo_url: Optional[str] = None
    max_members: Optional[int] = Field(None, ge=1, le=1000)


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    plan_tier: str
    settings: Optional[Dict[str, Any]] = None
    max_members: int
    logo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    member_count: Optional[int] = None

    class Config:
        from_attributes = True


class OrganizationSummary(BaseModel):
    """Lightweight org info for switcher dropdown."""
    id: str
    name: str
    slug: str
    plan_tier: str
    role: str  # Current user's role in this org

    class Config:
        from_attributes = True


# ── Membership Schemas ────────────────────────────────────────────

class MemberCreate(BaseModel):
    user_id: int
    role: str = Field(default="viewer", pattern=r"^(owner|admin|operator|viewer)$")


class MemberUpdate(BaseModel):
    role: str = Field(..., pattern=r"^(owner|admin|operator|viewer)$")


class MemberResponse(BaseModel):
    id: int
    organization_id: str
    user_id: int
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    role: str
    joined_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ── Invitation Schemas ────────────────────────────────────────────

class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = Field(default="viewer", pattern=r"^(admin|operator|viewer)$")


class InvitationResponse(BaseModel):
    id: int
    organization_id: str
    email: str
    role: str
    status: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InvitationAccept(BaseModel):
    token: str


# ── Tenant Context ────────────────────────────────────────────────

class TenantContext(BaseModel):
    """Injected into request state by TenantMiddleware."""
    organization_id: str
    user_id: int
    role: str
    permissions: List[str] = []
