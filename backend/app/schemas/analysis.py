from pydantic import BaseModel
from datetime import datetime

class AnalysisMetrics(BaseModel):
    commit_frequency: float | None = None
    contributor_count: int | None = None
    last_commit_date: datetime | None = None
    issue_count: int | None = None
    average_issue_response_time: float | None = None
    release_frequency: float | None = None
    vulnerability_count: int = 0
    critical_vulnerabilities: int = 0
    high_vulnerabilities: int = 0

class AnalysisScores(BaseModel):
    maintenance_score: float  # 0-100
    activity_score: float     # 0-100
    security_score: float     # 0-100
    overall_risk_level: str   # "low", "medium", "high"

class AnalysisResponse(BaseModel):
    id: int
    project_id: int
    metrics: AnalysisMetrics
    scores: AnalysisScores
    analyzed_at: datetime
    
    class Config:
        from_attributes = True

class AnalysisExplanation(BaseModel):
    """Explanation of why scores are what they are"""
    maintenance_explanation: str
    activity_explanation: str
    security_explanation: str
    overall_recommendation: str