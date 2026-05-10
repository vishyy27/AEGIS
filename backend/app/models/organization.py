"""
Phase 11.8.1: Multi-Tenant Organization Models.

Tables:
  - Organization: Top-level tenant entity with UUID PK
  - OrganizationMember: User ↔ Organization membership with roles
  - OrganizationInvitation: Token-based invitations with expiry

Design Decisions:
  - UUID primary key on Organization for globally unique tenant IDs
  - Slug field for URL-safe org routing (e.g., /org/acme/dashboard)
  - plan_tier for future feature gating
  - JSON settings for extensible org-level config
  - Composite unique constraint on (org_id, user_id) prevents duplicate membership
"""

import uuid
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, JSON,
    ForeignKey, UniqueConstraint, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Organization(Base):
    """Top-level tenant entity. All data is scoped to an organization."""
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    plan_tier = Column(String(20), default="free", nullable=False)  # free, team, enterprise
    settings = Column(JSON, nullable=True, default=dict)
    max_members = Column(Integer, default=5, nullable=False)
    logo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("OrganizationInvitation", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base):
    """User membership in an organization with role-based access."""
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), default="viewer", nullable=False)  # owner, admin, operator, viewer
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])


class OrganizationInvitation(Base):
    """Token-based org invitations with expiry and single-use semantics."""
    __tablename__ = "organization_invitations"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    role = Column(String(20), default="viewer", nullable=False)
    token = Column(String(64), unique=True, index=True, nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending, accepted, expired, revoked
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[invited_by])
