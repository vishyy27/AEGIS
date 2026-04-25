import hashlib
import hmac
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException, Header, BackgroundTasks
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from ..database import get_db
from ..config import settings
from ..services.cicd_integrations import detect_cicd_platform, normalize_pipeline_payload
from ..services.analysis_orchestrator import evaluate_deployment
from ..services.policy_engine import evaluate_from_analysis
from ..schemas.integration_schema import PolicyDecisionResponse
from ..models.deployment import Deployment

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


@router.post("/webhook", response_model=PolicyDecisionResponse)
async def webhook_receiver(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_aegis_token: str = Header(..., alias="X-AEGIS-TOKEN")
):
    """
    Webhook ingestion endpoint for CI/CD integrations.
    Returns policy decision after full analysis pipeline.
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
    analysis_response = evaluate_deployment(analysis_request, db, background_tasks)

    # Persist decision to deployment
    deployment = db.query(Deployment).filter(Deployment.id == analysis_response.deployment_id).first()

    # Evaluate policy decision
    policy_decision = evaluate_from_analysis(
        db_session=db,
        deployment=deployment,
        risk_score=analysis_response.risk_score,
        risk_level=analysis_response.risk_level,
        risk_factors=analysis_response.risk_factors,
        alert_severity=None,
        affected_modules=analysis_request.changed_files,
        historical_failures=analysis_request.historical_failures
    )

    if deployment:
        deployment.deployment_decision = policy_decision.decision
        deployment.decision_timestamp = datetime.utcnow()
        db.commit()

    return PolicyDecisionResponse(
        decision=policy_decision.decision,
        risk_score=policy_decision.risk_score,
        risk_level=policy_decision.risk_level,
        confidence_score=policy_decision.confidence_score,
        reasoning=policy_decision.reasoning,
        recommendations=policy_decision.recommendations,
        message=policy_decision.message,
        override_reason=policy_decision.override_reason,
        alert_severity=policy_decision.alert_severity,
        affected_modules=policy_decision.affected_modules,
    )