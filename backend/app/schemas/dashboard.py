from pydantic import BaseModel
from typing import List
from datetime import datetime

class DashboardSummary(BaseModel):
    total_projects: int
    total_analyzed: int
    low_risk_count: int
    medium_risk_count: int
    high_risk_count: int
    total_vulnerabilities: int
    critical_vulnerabilities: int
    recent_analyses: int

class ProjectScoreHistory(BaseModel):
    project_id: int
    project_name: str
    timeline: List[dict]  # [{date, maintenance_score, activity_score, security_score}]

class TimelineDataPoint(BaseModel):
    date: datetime
    maintenance_score: float | None = None
    activity_score: float | None = None
    security_score: float | None = None
    vulnerability_count: int = 0

class VulnerabilitySummary(BaseModel):
    project_id: int
    project_name: str
    total_vulnerabilities: int
    critical: int
    high: int
    medium: int
    low: int
    last_checked: datetime | None = None