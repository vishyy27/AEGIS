from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/environments", tags=["environments"])


class EnvironmentSwitchRequest(BaseModel):
    environment: str


@router.get("/")
def get_environments():
    return ["Production", "Staging", "Development"]


@router.post("/switch")
def switch_environment(request: EnvironmentSwitchRequest):
    # In a real app this might set a user session or cookie
    return {"status": f"Switched to {request.environment}"}
