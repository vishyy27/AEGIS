import hashlib
import hmac
from fastapi import APIRouter, Depends, Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from ..database import get_db
from ..config import settings
from ..services.cicd_integrations import detect_cicd_platform, normalize_pipeline_payload
from ..services.analysis_orchestrator import evaluate_deployment
from pydantic import BaseModel, ValidationError

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

# Security schemes
API_KEY_NAME = "X-AEGIS-TOKEN"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Constants
MAX_PAYLOAD_SIZE = 1 * 1024 * 1024  # 1MB limit for DOS protection

async def verify_security(request: Request, api_key: str = Security(api_key_header)):
    # 1. Size Limit Check
    body = await request.body()
    if len(body) > MAX_PAYLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Payload Too Large")
        
    headers = request.headers
    platform = detect_cicd_platform(dict(headers))
    
    # 2. GitHub HMAC validation (Optional phase 4 implementation)
    if platform == "github":
        signature = headers.get("X-Hub-Signature-256")
        if signature:
            expected_signature = "sha256=" + hmac.new(
                settings.GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, expected_signature):
                raise HTTPException(status_code=401, detail="Invalid GitHub signature")
            return platform
            
    # 3. Fallback to API Token check for all platforms
    if api_key != settings.AEGIS_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing X-AEGIS-TOKEN")
        
    return platform

@router.post("/webhook")
async def webhook_receiver(
    request: Request,
    db: Session = Depends(get_db)
):
    """Webhook ingestion endpoint for CI/CD integrations."""
    # Authenticate and Size check
    platform = await verify_security(request)
    
    try:
        # Load JSON payload
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    # Baseline payload validation
    # Explicit requirements: repository_name, commit_count, files_changed, commit_messages
    if platform == "generic":
        required_fields = ["repository_name", "commit_count", "files_changed", "commit_messages"]
        for field in required_fields:
            if field not in payload:
                raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Process Payload natively
    try:
        analysis_request = normalize_pipeline_payload(platform, payload)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error normalizing payload: {str(e)}")
        
    # Trigger Orchestrator Pipeline
    evaluate_deployment(analysis_request, db)
    
    return {"status": "success", "message": f"{platform} webhook processed and analysis triggered."}
