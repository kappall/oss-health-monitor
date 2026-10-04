from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from app.models.favorite import Favorite
from app.models.project import Project
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


class FavoriteService:
    """Service for managing project favorites
    """

    @staticmethod
    async def add_favorite(
        db: AsyncSession,
        user_id: int,
        project_id: int
    ) -> Favorite:
        """Add a project to user's favorites.

        Returns the Favorite ORM instance. Raises ValueError if project not found or not owned by user.
        """
        # Check project exists and belongs to user
        result = await db.execute(
            select(Project).where(
                and_(
                    Project.id == project_id,
                    Project.user_id == user_id
                )
            )
        )
        project = result.scalar_one_or_none()

        if not project:
            logger.debug("add_favorite: project %s not found for user %s", project_id, user_id)
            raise ValueError("Project not found")

        # Check existing favorite
        existing_result = await db.execute(
            select(Favorite).where(
                and_(
                    Favorite.user_id == user_id,
                    Favorite.project_id == project_id
                )
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            logger.debug("add_favorite: favorite already exists for user %s project %s", user_id, project_id)
            return existing

        # Create favorite (persist + atomically increment favorites_count)
        favorite = Favorite(user_id=user_id, project_id=project_id)
        db.add(favorite)

        # Prefer DB-level atomic increment (sa.update). Fallback to defensive approach only if update fails.
        try:
            await db.execute(
                update(Project)
                .where(Project.id == project_id)
                .values(favorites_count=(Project.favorites_count + 1))
            )
        except Exception:
            logger.exception("add_favorite: DB-level increment failed; fallback attempted")
            # Best-effort fallback (older schema / unexpected type)
            try:
                if hasattr(project, "favorites_count"):
                    project.favorites_count = (project.favorites_count or 0) + 1
            except Exception:
                logger.exception("add_favorite: fallback increment failed")

        # Commit and refresh
        try:
            await db.commit()
            await db.refresh(favorite)
        except Exception:
            await db.rollback()
            logger.exception("add_favorite: commit failed for user %s project %s", user_id, project_id)
            raise

        return favorite

    @staticmethod
    async def remove_favorite(
        db: AsyncSession,
        user_id: int,
        project_id: int
    ) -> bool:
        """Remove a project from user's favorites. Returns True if removed, False if not found."""
        result = await db.execute(
            select(Favorite).where(
                and_(
                    Favorite.user_id == user_id,
                    Favorite.project_id == project_id
                )
            )
        )
        favorite = result.scalar_one_or_none()

        if not favorite:
            logger.debug("remove_favorite: favorite not found for user %s project %s", user_id, project_id)
            return False

        # Update project favorite count if possible
        project_result = await db.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()
        try:
            if project and hasattr(project, "favorites_count"):
                try:
                    if project.favorites_count and project.favorites_count > 0:
                        project.favorites_count -= 1
                except Exception:
                    # Defensive: if type mismatch, skip decrement
                    logger.debug("remove_favorite: unexpected type for project.favorites_count")
        except Exception as e:
            logger.exception("remove_favorite: failed updating project favorite count: %s", e)

        # On remove: atomically decrement (only when > 0) and delete favorite
        try:
            await db.execute(
                update(Project)
                .where(Project.id == project_id, Project.favorites_count > 0)
                .values(favorites_count=(Project.favorites_count - 1))
            )
        except Exception:
            logger.exception("remove_favorite: DB-level decrement failed; fallback attempted")
            # fallback handled implicitly if necessary
        try:
            await db.delete(favorite)
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("remove_favorite: commit failed for deleting favorite user %s project %s", user_id, project_id)
            raise

        return True

    @staticmethod
    async def get_user_favorites(
        db: AsyncSession,
        user_id: int
    ) -> List[Tuple[Project, Favorite]]:
        """Get all favorited projects for a user.

        Returns a list of (Project, Favorite) tuples ordered by Favorite.created_at desc.
        """
        result = await db.execute(
            select(Project, Favorite)
            .join(Favorite, Favorite.project_id == Project.id)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
        )

        return result.all()

    @staticmethod
    async def is_favorited(
        db: AsyncSession,
        user_id: int,
        project_id: int
    ) -> bool:
        """Check if a project is favorited by user"""
        result = await db.execute(
            select(Favorite).where(
                and_(
                    Favorite.user_id == user_id,
                    Favorite.project_id == project_id
                )
            )
        )

        return result.scalar_one_or_none() is not None
