from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.favorite import (
    FavoriteCreate,
    FavoriteResponse,
    FavoriteProjectResponse
)
from app.services.favorite_service import FavoriteService
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])

@router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a project to favorites.

    Returns the created Favorite resource.
    """
    try:
        result = await FavoriteService.add_favorite(
            db, current_user.id, favorite.project_id
        )
        return result
    except ValueError as e:
        # Project not found -> 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a project from favorites.
    """
    success = await FavoriteService.remove_favorite(
        db, current_user.id, project_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )

    return None

@router.get("/", response_model=List[FavoriteProjectResponse])
async def list_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all favorited projects for current user.

    Returns projects with their risk scores and favorite timestamp.
    TODO: paginating the result for users with many favorites.
    """
    favorites = await FavoriteService.get_user_favorites(db, current_user.id)

    result = [
        FavoriteProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            repository_url=project.repository_url,
            overall_risk_level=project.overall_risk_level,
            maintenance_score=project.maintenance_score,
            activity_score=project.activity_score,
            security_score=project.security_score,
            last_analyzed_at=project.last_analyzed_at,
            favorited_at=favorite.created_at
        )
        for project, favorite in favorites
    ]

    return result

@router.get("/check/{project_id}", response_model=dict)
async def check_favorite(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if a project is favorited.

    Returns {"is_favorited": bool}.
    TODO: consider using a small response schema instead of plain dict for better docs/validation.
    """
    is_fav = await FavoriteService.is_favorited(db, current_user.id, project_id)
    return {"is_favorited": is_fav}
