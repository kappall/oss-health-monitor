from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.project import (
    ProjectSubmit,
    ProjectResponse,
    ProjectListResponse
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.post("/submit", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def submit_project(
    submission: ProjectSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a repository or package for analysis
    
    Accepts:
    - GitHub URL: https://github.com/owner/repo or owner/repo
    - NPM package: npm:package-name
    - PyPI package: pypi:package-name
    """
    try:
        project = await ProjectService.submit_project(db, current_user, submission)
        return project
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit project: {str(e)}"
        )

@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all projects for the current user"""
    skip = (page - 1) * page_size
    projects, total = await ProjectService.get_user_projects(
        db, current_user.id, skip, page_size
    )
    
    return ProjectListResponse(
        projects=projects,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific project by ID"""
    project = await ProjectService.get_project_by_id(db, project_id, current_user.id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a project"""
    success = await ProjectService.delete_project(db, project_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return None