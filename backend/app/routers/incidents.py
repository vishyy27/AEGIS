from fastapi import APIRouter

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.get("/")
async def get_incidents():
    return {"incidents": []}
