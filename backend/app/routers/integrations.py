import hashlib
import hmac
from fastapi import APIRouter, Depends, Request, HTTPException, Header
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from ..database import get_db
from ..config import settings
from ..services.cicd_integrations import detect_cicd_platform, normalize_pipeline_payload
from ..services.analysis_orchestrator import evaluate_deployment

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

# Constants
MAX_PAYLOAD_SIZE = 1 * 1024 * 1024  # 1MB DOS protection


async def verify_security(request: Request, api_key: str):
    """
    Security validation for incoming CI/CD webhooks.
    """

    # 1️⃣ Payload size protection
    body = await request.body()
    if len(body) > MAX_PAYLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Payload Too Large")

    headers = request.headers
    platform = detect_cicd_platform(dict(headers))

    # 2️⃣ GitHub signature verification (optional)
    if platform == "github":
        signature = headers.get("X-Hub-Signature-256")

        if signature and settings.GITHUB_WEBHOOK_SECRET:
            expected_signature = "sha256=" + hmac.new(
                settings.GITHUB_WEBHOOK_SECRET.encode(),
                body,
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                raise HTTPException(status_code=401, detail="Invalid GitHub signature")

            return platform

    # 3️⃣ API token verification
    if api_key != settings.AEGIS_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing X-AEGIS-TOKEN")

    return platform


@router.post("/webhook")
async def webhook_receiver(
    request: Request,
    db: Session = Depends(get_db),
    x_aegis_token: str = Header(..., alias="X-AEGIS-TOKEN")
):
    """
    Webhook ingestion endpoint for CI/CD integrations.
    """

    # Authenticate request
    platform = await verify_security(request, x_aegis_token)

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Baseline validation for generic pipelines
    if platform == "generic":
        required_fields = [
            "repository_name",
            "commit_count",
            "files_changed",
            "commit_messages"
        ]

        for field in required_fields:
            if field not in payload:
                raise HTTPException(
                    status_code=422,
                    detail=f"Missing required field: {field}"
                )

    # Normalize CI/CD payload
    try:
        analysis_request = normalize_pipeline_payload(platform, payload)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Error normalizing payload: {str(e)}"
        )

    # Trigger analysis pipeline
    evaluate_deployment(analysis_request, db)

    return {
        "status": "success",
        "message": f"{platform} webhook processed and analysis triggered."
    }