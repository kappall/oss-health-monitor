from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.analysis import Analysis
from app.api.dependencies import get_current_user
from app.schemas.analysis import AnalysisResponse, AnalysisExplanation
from app.services.github_analysis_service import GitHubAnalysisService
from app.services.analysis_service import AnalysisScoreService
from datetime import datetime, timezone

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

@router.post("/analyze/{project_id}", response_model=AnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a project and calculate risk scores
    
    Currently supports GitHub repositories.
    Fetches:
    - Commit history and frequency
    - Contributor count
    - Issue activity
    - Release cadence
    - Security vulnerabilities
    """
    
    # Get project
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    try:
        # TODO: Only GitHub repos supported for now
        if "github.com" not in project.repository_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only GitHub repositories are currently supported for analysis"
            )
        
        analysis = await GitHubAnalysisService.analyze_repository(
            db,
            project,
            current_user.github_token
        )
        
        return analysis
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.get("/explain/{project_id}", response_model=AnalysisExplanation)
async def get_analysis_explanation(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get explanation of analysis scores for a project
    
    Returns human-readable explanations for:
    - Maintenance score
    - Activity score
    - Security score
    - Overall recommendation
    """
    
    # Get project
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if not project.last_analyzed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has not been analyzed yet"
        )

    # Find latest analysis record for this project
    res = await db.execute(
        select(Analysis).where(Analysis.project_id == project.id).order_by(Analysis.created_at.desc())
    )
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No analysis found for this project"
        )
    
    # compute days since last commit for the explanation
    if analysis.last_commit_date:
        last_commit_days = int((datetime.now(timezone.utc) - analysis.last_commit_date).days)
    else:
        last_commit_days = 999
    
    _, maintenance_explanation = AnalysisScoreService.calculate_maintenance_score(
        contributor_count=analysis.contributor_count or 0,
        last_commit_days_ago=last_commit_days,
        release_frequency=analysis.release_frequency or 0.0
    )
    _, activity_explanation = AnalysisScoreService.calculate_activity_score(
        issue_count=analysis.issue_count or 0,
        average_issue_response_time=analysis.average_issue_response_time or 24.0,
        commit_frequency=analysis.commit_frequency or 0.0
    )
    _, security_explanation = AnalysisScoreService.calculate_security_score(
        critical_vulnerabilities=analysis.critical_vulnerabilities or 0,
        high_vulnerabilities=analysis.high_vulnerabilities or 0,
        medium_vulnerabilities=analysis.medium_vulnerabilities or 0,
        total_vulnerabilities=analysis.vulnerability_count or 0
    )
    
    risk_level = analysis.overall_risk_level or AnalysisScoreService.calculate_overall_risk_level(
        maintenance_score=analysis.maintenance_score or 0.0,
        activity_score=analysis.activity_score or 0.0,
        security_score=analysis.security_score or 0.0
    )
    
    if risk_level == "low":
        overall_recommendation = "This dependency appears to be safe and well-maintained. It's a good candidate for adoption."
    elif risk_level == "medium":
        overall_recommendation = "This dependency has moderate risk. Consider your use case and evaluate the trade-offs."
    else:
        overall_recommendation = "This dependency has high risk. Consider alternatives or implement additional monitoring."
    
    return AnalysisExplanation(
        maintenance_explanation=maintenance_explanation,
        activity_explanation=activity_explanation,
        security_explanation=security_explanation,
        overall_recommendation=overall_recommendation
    )