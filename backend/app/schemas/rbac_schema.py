"""
Phase 11.8.2: Advanced RBAC Pydantic Schemas.

Contracts for Permissions, Roles, and Role Management.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Any
from datetime import datetime


class PermissionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category: str

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)


class RoleCreate(RoleBase):
    permission_ids: List[str] = Field(..., min_length=1)


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    permission_ids: Optional[List[str]] = None


class RoleResponse(RoleBase):
    id: int
    organization_id: Optional[str]
    is_system: bool
    created_at: datetime
    permissions: List[PermissionResponse]

    model_config = ConfigDict(from_attributes=True)

    @field_validator('permissions', mode='before')
    @classmethod
    def extract_permissions(cls, v: Any) -> Any:
        if not v:
            return []
        extracted = []
        for item in v:
            if hasattr(item, "permission") and item.permission:
                extracted.append(item.permission)
            elif isinstance(item, dict) and "permission" in item:
                extracted.append(item["permission"])
            else:
                extracted.append(item)
        return extracted


class MemberRoleAssign(BaseModel):
    role_ids: List[int] = Field(..., min_length=1)
