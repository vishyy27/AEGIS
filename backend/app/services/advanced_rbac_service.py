"""
Phase 11.8.2: Advanced RBAC Service.

Core engine for permission resolution, role management, and system bootstrap.
Utilizes an LRU cache to prevent database hits on every request for permission checks.
"""

import logging
from typing import List, Set, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from cachetools import TTLCache, cached
from ..models.organization import OrganizationMember
from ..models.rbac import Permission, Role, RolePermission, MemberRole
from ..schemas.rbac_schema import RoleCreate, RoleUpdate, RoleResponse

logger = logging.getLogger("aegis.rbac_engine")

# Centralized permission definitions.
SYSTEM_PERMISSIONS = [
    # Deployments
    {"id": "deployment:view", "name": "View Deployments", "description": "Can view deployment logs and metrics", "category": "Deployments"},
    {"id": "deployment:execute", "name": "Execute Deployments", "description": "Can trigger and manage deployments", "category": "Deployments"},
    # Incidents
    {"id": "incident:view", "name": "View Incidents", "description": "Can view active and past incidents", "category": "Incidents"},
    {"id": "incident:manage", "name": "Manage Incidents", "description": "Can resolve, update, and manage incidents", "category": "Incidents"},
    # Telemetry
    {"id": "telemetry:view", "name": "View Telemetry", "description": "Can view real-time metrics and logs", "category": "Telemetry"},
    # Intelligence / Simulations
    {"id": "simulation:view", "name": "View Simulations", "description": "Can view past simulation results", "category": "Intelligence"},
    {"id": "simulation:run", "name": "Run Simulations", "description": "Can trigger new synthetic simulations", "category": "Intelligence"},
    {"id": "replay:view", "name": "View Replays", "description": "Can access deployment replay timelines", "category": "Intelligence"},
    {"id": "assistant:use", "name": "Use AI Assistant", "description": "Can interact with the AI Copilot", "category": "Intelligence"},
    # Admin / Org
    {"id": "org:manage", "name": "Manage Organization", "description": "Can edit org settings and manage billing", "category": "Administration"},
    {"id": "member:manage", "name": "Manage Members", "description": "Can invite, remove, and assign roles to members", "category": "Administration"},
    {"id": "audit:view", "name": "View Audit Logs", "description": "Can view enterprise audit trails", "category": "Administration"},
]

# System Role Templates
SYSTEM_ROLES = {
    "super_admin": ["*"],  # Special case: all permissions
    "org_admin": ["org:manage", "member:manage", "audit:view", "deployment:execute", "deployment:view", "incident:manage", "incident:view", "telemetry:view", "simulation:run", "simulation:view", "replay:view", "assistant:use"],
    "deployment_operator": ["deployment:view", "deployment:execute", "telemetry:view", "incident:view", "simulation:run", "simulation:view", "replay:view", "assistant:use"],
    "incident_manager": ["incident:view", "incident:manage", "telemetry:view", "replay:view", "assistant:use"],
    "ai_analyst": ["simulation:run", "simulation:view", "replay:view", "telemetry:view", "incident:view", "assistant:use"],
    "viewer": ["deployment:view", "telemetry:view", "incident:view", "simulation:view", "replay:view"],
}

# Cache for permission resolution: (org_id, user_id) -> Set[permission_ids]
# TTL set to 5 minutes to balance performance and staleness
permission_cache = TTLCache(maxsize=1000, ttl=300)


class AdvancedRBACService:

    def bootstrap_system_roles(self, db: Session):
        """Initializes system permissions and default roles in the database."""
        try:
            # 1. Upsert Permissions
            existing_perms = {p.id: p for p in db.query(Permission).all()}
            for p_def in SYSTEM_PERMISSIONS:
                if p_def["id"] not in existing_perms:
                    db.add(Permission(**p_def))
                else:
                    # Update metadata if changed
                    ep = existing_perms[p_def["id"]]
                    ep.name = p_def["name"]
                    ep.description = p_def["description"]
                    ep.category = p_def["category"]
            db.flush()

            all_perm_ids = [p["id"] for p in SYSTEM_PERMISSIONS]

            # 2. Upsert System Roles
            for role_name, perms in SYSTEM_ROLES.items():
                role = db.query(Role).filter(Role.name == role_name, Role.is_system == True).first()
                if not role:
                    role = Role(name=role_name, is_system=True, description=f"System default {role_name} role")
                    db.add(role)
                    db.flush()
                
                # Clear existing and remap
                db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
                
                target_perms = all_perm_ids if "*" in perms else perms
                for p_id in target_perms:
                    if p_id in all_perm_ids:  # Safety check
                        db.add(RolePermission(role_id=role.id, permission_id=p_id))
            
            db.commit()
            logger.info("[RBAC] System roles and permissions bootstrapped successfully")
        except Exception as e:
            db.rollback()
            logger.error(f"[RBAC] Failed to bootstrap system roles: {e}")

    # ── Permission Resolution & Enforcement ─────────────────────────

    @cached(cache=permission_cache)
    def resolve_user_permissions(self, db: Session, org_id: str, user_id: int) -> Set[str]:
        """
        Calculates the effective permissions for a user in an org.
        Cached via TTLCache for fast middleware resolution.
        """
        # 1. Get member record
        member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.is_active == True
        ).first()
        
        if not member:
            return set()

        permissions = set()

        # 2. Get permissions from new MemberRole mapping
        member_roles = db.query(RolePermission.permission_id)\
            .join(MemberRole, MemberRole.role_id == RolePermission.role_id)\
            .filter(MemberRole.member_id == member.id).all()
        
        for (p_id,) in member_roles:
            permissions.add(p_id)

        # 3. Fallback/Migration: If no MemberRoles exist, fallback to legacy string role
        if not permissions and member.role:
            # Map legacy role string to system role name
            legacy_map = {
                "owner": "super_admin",
                "admin": "org_admin",
                "operator": "deployment_operator",
                "viewer": "viewer"
            }
            system_role_name = legacy_map.get(member.role, "viewer")
            
            # Fetch permissions for that system role
            system_role_perms = db.query(RolePermission.permission_id)\
                .join(Role, Role.id == RolePermission.role_id)\
                .filter(Role.name == system_role_name, Role.is_system == True).all()
            
            for (p_id,) in system_role_perms:
                permissions.add(p_id)

        return permissions

    def invalidate_cache(self, org_id: str, user_id: int):
        """Force drops the user's permission cache."""
        cache_key = (self.resolve_user_permissions, db_hash_placeholder, org_id, user_id)
        # Note: cachetools cached decorator doesn't expose easy targeted invalidation based on args easily.
        # For this prototype, we'll clear the whole cache on permission mutations, or let TTL handle it.
        permission_cache.clear()

    # ── Custom Role Management ──────────────────────────────────────

    def create_custom_role(self, db: Session, org_id: str, data: RoleCreate) -> Role:
        # Verify permissions exist
        valid_perms = db.query(Permission.id).filter(Permission.id.in_(data.permission_ids)).all()
        valid_perm_ids = {p[0] for p in valid_perms}
        
        if len(valid_perm_ids) != len(data.permission_ids):
            raise ValueError("One or more invalid permission IDs provided")

        role = Role(
            organization_id=org_id,
            name=data.name,
            description=data.description,
            is_system=False
        )
        db.add(role)
        db.flush()

        for p_id in valid_perm_ids:
            db.add(RolePermission(role_id=role.id, permission_id=p_id))
        
        db.commit()
        db.refresh(role)
        return role

    def get_org_roles(self, db: Session, org_id: str) -> List[Role]:
        # Return both system roles and org custom roles
        return db.query(Role).filter(
            (Role.organization_id == org_id) | (Role.is_system == True)
        ).all()

    def assign_roles_to_member(self, db: Session, org_id: str, member_id: int, role_ids: List[int]):
        member = db.query(OrganizationMember).filter(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == org_id
        ).first()
        
        if not member:
            raise ValueError("Member not found in organization")

        # Verify roles exist and belong to org/system
        roles = db.query(Role).filter(
            Role.id.in_(role_ids),
            (Role.organization_id == org_id) | (Role.is_system == True)
        ).all()

        if len(roles) != len(role_ids):
            raise ValueError("One or more roles are invalid or not accessible")

        # Clear existing
        db.query(MemberRole).filter(MemberRole.member_id == member_id).delete()
        
        # Add new
        for r_id in role_ids:
            db.add(MemberRole(member_id=member_id, role_id=r_id))
            
        db.commit()
        # Invalidate cache for this user
        self.invalidate_cache(org_id, member.user_id)


rbac_service = AdvancedRBACService()

# Placeholder for cache key generation
db_hash_placeholder = None 
