"""
Phase 11.9: RBAC Service. Basic role-based access control for enterprise readiness.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..models.phase11_models import AuditLog

logger = logging.getLogger("aegis.rbac")

# Role definitions
ROLES = {
    "admin": {"level": 100, "permissions": ["*"]},
    "operator": {"level": 50, "permissions": ["deploy", "view", "simulate", "replay", "assistant"]},
    "viewer": {"level": 10, "permissions": ["view", "replay", "assistant"]},
}


class RBACService:
    def check_permission(self, role: str, action: str) -> bool:
        role_def = ROLES.get(role, ROLES["viewer"])
        if "*" in role_def["permissions"]:
            return True
        return action in role_def["permissions"]

    def log_audit(self, db: Session, action: str, actor: str = "system",
                  resource_type: str = None, resource_id: str = None,
                  details: Dict = None, ip_address: str = None):
        try:
            entry = AuditLog(
                action=action, actor=actor,
                resource_type=resource_type, resource_id=resource_id,
                details=details, ip_address=ip_address,
            )
            db.add(entry)
            db.commit()
        except Exception as e:
            logger.warning(f"[RBAC] audit_log_failed: {e}")

    def get_audit_trail(self, db: Session, limit: int = 50,
                        action: str = None, actor: str = None) -> List[Dict[str, Any]]:
        query = db.query(AuditLog)
        if action:
            query = query.filter(AuditLog.action == action)
        if actor:
            query = query.filter(AuditLog.actor == actor)
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        return [{
            "id": l.id, "action": l.action, "actor": l.actor,
            "resource_type": l.resource_type, "resource_id": l.resource_id,
            "details": l.details, "timestamp": l.timestamp.isoformat() if l.timestamp else None,
        } for l in logs]


rbac_service = RBACService()
