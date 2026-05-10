"""
Phase 11.8.2: Advanced RBAC Models.

Tables:
  - Permission: Granular system actions (e.g., 'deployment:execute').
  - Role: Named collection of permissions. Can be system-wide (org_id=NULL) or custom (org_id defined).
  - RolePermission: Many-to-many mapping of roles to permissions.
  - MemberRole: Many-to-many mapping of OrganizationMembers to Roles.

Design Decisions:
  - DB-backed granular permissions ensure enterprise auditability.
  - System roles act as immutable templates.
  - Custom roles enable enterprise orgs to define specific permission sets.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Permission(Base):
    """Granular action that can be performed in the system."""
    __tablename__ = "permissions"

    id = Column(String(100), primary_key=True)  # e.g., 'deployment:execute'
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    category = Column(String(50), nullable=False)  # e.g., 'Deployments', 'Settings'

    # Relationships
    role_mappings = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class Role(Base):
    """Named collection of permissions. System roles have organization_id=NULL."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_org_role_name"),
    )

    # Relationships
    organization = relationship("Organization")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    member_mappings = relationship("MemberRole", back_populates="role", cascade="all, delete-orphan")


class RolePermission(Base):
    """Mapping between roles and permissions."""
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(String(100), ForeignKey("permissions.id"), primary_key=True)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_mappings")


class MemberRole(Base):
    """Mapping between organization members and roles. Replaces single string role."""
    __tablename__ = "member_roles"

    member_id = Column(Integer, ForeignKey("organization_members.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    member = relationship("OrganizationMember") # Assuming OrganizationMember has 'roles' relation added
    role = relationship("Role", back_populates="member_mappings")
