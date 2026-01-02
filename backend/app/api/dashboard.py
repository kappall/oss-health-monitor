from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.dashboard import (
    DashboardSummary,
    ProjectScoreHistory,
    VulnerabilitySummary
)
from app.services.dashboard_service import DashboardService
from typing import List

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard summary statistics
    
    Returns:
    - Total projects count
    - Analyzed projects count
    - Risk level distribution (low/medium/high)
    - Total vulnerabilities
    - Recent analysis activity
    """
    summary = await DashboardService.get_dashboard_summary(db, current_user.id)
    return summary

@router.get("/timeline/{project_id}", response_model=ProjectScoreHistory)
async def get_project_timeline(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical score timeline for a project
    """
    try:
        timeline = await DashboardService.get_project_timeline(
            db, project_id, current_user.id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return timeline

@router.get("/vulnerabilities", response_model=List[VulnerabilitySummary])
async def get_vulnerabilities_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get vulnerability summary for all user projects
    
    Returns list of projects with:
    - Vulnerability counts by severity
    - Last check date
    """
    summaries = await DashboardService.get_vulnerabilities_summary(
        db, current_user.id
    )
    return summaries
