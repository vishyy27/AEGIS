"""
Phase 11.8.1: Organization Service.

Handles all organization lifecycle operations:
  - Organization CRUD
  - Member management (add/remove/update role)
  - Invitation flow (create/accept/revoke)
  - Organization resolution from user context

Design:
  - Stateless service, receives DB session via dependency injection
  - All queries are org-scoped where applicable
  - Audit logging on all mutating operations
  - Token-based invitations with configurable TTL
"""

import uuid
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.organization import Organization, OrganizationMember, OrganizationInvitation
from ..models.user import User
from ..schemas.organization_schema import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationSummary, MemberResponse, InvitationCreate, InvitationResponse,
)

logger = logging.getLogger("aegis.organization")

INVITATION_TTL_HOURS = 72

# Role hierarchy for permission checks
ROLE_HIERARCHY = {
    "owner": 100,
    "admin": 75,
    "operator": 50,
    "viewer": 10,
}


class OrganizationService:

    # ── Organization CRUD ─────────────────────────────────────────

    def create_organization(
        self, db: Session, data: OrganizationCreate, creator_user_id: int
    ) -> OrganizationResponse:
        """Create org + auto-add creator as owner."""
        # Check slug uniqueness
        existing = db.query(Organization).filter(Organization.slug == data.slug).first()
        if existing:
            raise ValueError(f"Organization slug '{data.slug}' already taken")

        org = Organization(
            id=str(uuid.uuid4()),
            name=data.name,
            slug=data.slug,
            plan_tier=data.plan_tier,
            settings=data.settings or {},
        )
        db.add(org)
        db.flush()

        # Creator becomes owner
        member = OrganizationMember(
            organization_id=org.id,
            user_id=creator_user_id,
            role="owner",
        )
        db.add(member)
        db.commit()
        db.refresh(org)

        logger.info(f"[ORG] created org={org.slug} id={org.id} by user={creator_user_id}")

        return OrganizationResponse(
            id=org.id, name=org.name, slug=org.slug,
            plan_tier=org.plan_tier, settings=org.settings,
            max_members=org.max_members, logo_url=org.logo_url,
            is_active=org.is_active, created_at=org.created_at,
            updated_at=org.updated_at, member_count=1,
        )

    def get_organization(self, db: Session, org_id: str) -> Optional[OrganizationResponse]:
        org = db.query(Organization).filter(Organization.id == org_id, Organization.is_active == True).first()
        if not org:
            return None
        member_count = db.query(func.count(OrganizationMember.id)).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.is_active == True
        ).scalar()
        return OrganizationResponse(
            id=org.id, name=org.name, slug=org.slug,
            plan_tier=org.plan_tier, settings=org.settings,
            max_members=org.max_members, logo_url=org.logo_url,
            is_active=org.is_active, created_at=org.created_at,
            updated_at=org.updated_at, member_count=member_count,
        )

    def get_organization_by_slug(self, db: Session, slug: str) -> Optional[Organization]:
        return db.query(Organization).filter(
            Organization.slug == slug, Organization.is_active == True
        ).first()

    def update_organization(
        self, db: Session, org_id: str, data: OrganizationUpdate
    ) -> Optional[OrganizationResponse]:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return None
        if data.name is not None:
            org.name = data.name
        if data.settings is not None:
            org.settings = data.settings
        if data.logo_url is not None:
            org.logo_url = data.logo_url
        if data.max_members is not None:
            org.max_members = data.max_members
        db.commit()
        db.refresh(org)
        return self.get_organization(db, org_id)

    def get_user_organizations(self, db: Session, user_id: int) -> List[OrganizationSummary]:
        """Get all orgs a user belongs to — used for org switcher."""
        memberships = (
            db.query(OrganizationMember, Organization)
            .join(Organization, OrganizationMember.organization_id == Organization.id)
            .filter(
                OrganizationMember.user_id == user_id,
                OrganizationMember.is_active == True,
                Organization.is_active == True,
            )
            .all()
        )
        return [
            OrganizationSummary(
                id=org.id, name=org.name, slug=org.slug,
                plan_tier=org.plan_tier, role=member.role,
            )
            for member, org in memberships
        ]

    # ── Member Management ─────────────────────────────────────────

    def get_members(self, db: Session, org_id: str) -> List[MemberResponse]:
        members = (
            db.query(OrganizationMember, User)
            .join(User, OrganizationMember.user_id == User.id)
            .filter(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.is_active == True,
            )
            .all()
        )
        return [
            MemberResponse(
                id=m.id, organization_id=m.organization_id,
                user_id=m.user_id, user_email=u.email, user_name=u.name,
                role=m.role, joined_at=m.joined_at, is_active=m.is_active,
            )
            for m, u in members
        ]

    def update_member_role(
        self, db: Session, org_id: str, user_id: int, new_role: str, actor_role: str
    ) -> Optional[MemberResponse]:
        """Update member role. Actor must outrank target role."""
        if ROLE_HIERARCHY.get(actor_role, 0) <= ROLE_HIERARCHY.get(new_role, 0):
            raise PermissionError("Cannot assign role equal to or higher than own")

        member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.is_active == True,
        ).first()
        if not member:
            return None

        # Cannot demote owner unless another owner exists
        if member.role == "owner":
            owner_count = db.query(func.count(OrganizationMember.id)).filter(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.role == "owner",
                OrganizationMember.is_active == True,
            ).scalar()
            if owner_count <= 1:
                raise ValueError("Cannot demote last owner")

        member.role = new_role
        db.commit()
        db.refresh(member)
        user = db.query(User).filter(User.id == user_id).first()
        return MemberResponse(
            id=member.id, organization_id=member.organization_id,
            user_id=member.user_id, user_email=user.email if user else None,
            user_name=user.name if user else None, role=member.role,
            joined_at=member.joined_at, is_active=member.is_active,
        )

    def remove_member(self, db: Session, org_id: str, user_id: int) -> bool:
        member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
        ).first()
        if not member:
            return False
        if member.role == "owner":
            owner_count = db.query(func.count(OrganizationMember.id)).filter(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.role == "owner",
                OrganizationMember.is_active == True,
            ).scalar()
            if owner_count <= 1:
                raise ValueError("Cannot remove last owner")
        member.is_active = False
        db.commit()
        return True

    # ── Invitation Flow ───────────────────────────────────────────

    def create_invitation(
        self, db: Session, org_id: str, data: InvitationCreate, inviter_id: int
    ) -> InvitationResponse:
        # Check member limit
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise ValueError("Organization not found")
        member_count = db.query(func.count(OrganizationMember.id)).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.is_active == True,
        ).scalar()
        if member_count >= org.max_members:
            raise ValueError(f"Organization member limit ({org.max_members}) reached")

        # Check duplicate pending invite
        existing = db.query(OrganizationInvitation).filter(
            OrganizationInvitation.organization_id == org_id,
            OrganizationInvitation.email == data.email,
            OrganizationInvitation.status == "pending",
        ).first()
        if existing:
            raise ValueError(f"Pending invitation already exists for {data.email}")

        invitation = OrganizationInvitation(
            organization_id=org_id,
            email=data.email,
            role=data.role,
            token=secrets.token_urlsafe(48),
            invited_by=inviter_id,
            expires_at=datetime.utcnow() + timedelta(hours=INVITATION_TTL_HOURS),
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        logger.info(f"[ORG] invitation created org={org_id} email={data.email}")

        return InvitationResponse(
            id=invitation.id, organization_id=invitation.organization_id,
            email=invitation.email, role=invitation.role,
            status=invitation.status, expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )

    def accept_invitation(self, db: Session, token: str, user_id: int) -> Optional[MemberResponse]:
        invitation = db.query(OrganizationInvitation).filter(
            OrganizationInvitation.token == token,
            OrganizationInvitation.status == "pending",
        ).first()
        if not invitation:
            return None
        if invitation.expires_at < datetime.utcnow():
            invitation.status = "expired"
            db.commit()
            return None

        # Check not already member
        existing_member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == invitation.organization_id,
            OrganizationMember.user_id == user_id,
        ).first()
        if existing_member:
            if existing_member.is_active:
                raise ValueError("Already a member of this organization")
            existing_member.is_active = True
            existing_member.role = invitation.role
        else:
            member = OrganizationMember(
                organization_id=invitation.organization_id,
                user_id=user_id,
                role=invitation.role,
                invited_by=invitation.invited_by,
            )
            db.add(member)

        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        db.commit()

        user = db.query(User).filter(User.id == user_id).first()
        member_record = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == invitation.organization_id,
            OrganizationMember.user_id == user_id,
        ).first()

        logger.info(f"[ORG] invitation accepted org={invitation.organization_id} user={user_id}")

        return MemberResponse(
            id=member_record.id, organization_id=member_record.organization_id,
            user_id=member_record.user_id,
            user_email=user.email if user else None,
            user_name=user.name if user else None,
            role=member_record.role, joined_at=member_record.joined_at,
            is_active=member_record.is_active,
        )

    def revoke_invitation(self, db: Session, org_id: str, invitation_id: int) -> bool:
        invitation = db.query(OrganizationInvitation).filter(
            OrganizationInvitation.id == invitation_id,
            OrganizationInvitation.organization_id == org_id,
            OrganizationInvitation.status == "pending",
        ).first()
        if not invitation:
            return False
        invitation.status = "revoked"
        db.commit()
        return True

    def get_pending_invitations(self, db: Session, org_id: str) -> List[InvitationResponse]:
        invitations = db.query(OrganizationInvitation).filter(
            OrganizationInvitation.organization_id == org_id,
            OrganizationInvitation.status == "pending",
        ).order_by(OrganizationInvitation.created_at.desc()).all()
        return [
            InvitationResponse(
                id=i.id, organization_id=i.organization_id,
                email=i.email, role=i.role, status=i.status,
                expires_at=i.expires_at, created_at=i.created_at,
            )
            for i in invitations
        ]

    # ── Tenant Resolution ─────────────────────────────────────────

    def get_user_membership(
        self, db: Session, org_id: str, user_id: int
    ) -> Optional[OrganizationMember]:
        """Resolve user's membership + role in given org. Used by middleware."""
        return db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.is_active == True,
        ).first()

    def ensure_default_organization(self, db: Session, default_org_id: str) -> Organization:
        """Create default org if it doesn't exist. Used in migration/startup."""
        org = db.query(Organization).filter(Organization.id == default_org_id).first()
        if not org:
            org = Organization(
                id=default_org_id,
                name="Default Organization",
                slug="default",
                plan_tier="enterprise",
                max_members=1000,
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            logger.info(f"[ORG] default org created id={default_org_id}")
        return org


organization_service = OrganizationService()
