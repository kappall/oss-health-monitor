from pydantic import BaseModel
from datetime import datetime

class FavoriteCreate(BaseModel):
    project_id: int

class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    project_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class FavoriteProjectResponse(BaseModel):
    """Project response with favorite status"""
    id: int
    name: str
    description: str | None = None
    repository_url: str
    overall_risk_level: str | None = None
    maintenance_score: float | None = None
    activity_score: float | None = None
    security_score: float | None = None
    last_analyzed_at: datetime | None = None
    favorited_at: datetime
    
    class Config:
        from_attributes = True

class FavoriteCheckResponse(BaseModel):
    is_favorited: bool
    favorited_at: datetime | None = None
