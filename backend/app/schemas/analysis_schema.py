from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class RecommendationSchema(BaseModel):
    message: str
    priority: str
    category: str
    affected_module: Optional[str] = None


class AnalysisRequest(BaseModel):
    repo_name: str
    commit_count: int
    files_changed: int
    code_churn: int
    test_coverage: float
    dependency_updates: int
    historical_failures: int
    deployment_frequency: int
    changed_files: List[str] = []
    commit_messages: List[str] = []
    lines_added: int = 0
    lines_deleted: int = 0
    
    # Phase 4 Integrations Fields
    pipeline_source: str = None
    branch_name: str = None
    commit_hash: str = None
    deployment_environment: str = None


class AnalysisResponse(BaseModel):
    deployment_id: int
    risk_score: float
    risk_level: str
    risk_factors: List[str]
    recommendations: List[str]
    context_recommendations: List[RecommendationSchema] = []
