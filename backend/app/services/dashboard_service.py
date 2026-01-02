from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta, timezone
import logging

from app.models.project import Project
from app.models.analysis import Analysis
from app.models.favorite import Favorite
from app.schemas.dashboard import (
    DashboardSummary,
    ProjectScoreHistory,
    TimelineDataPoint,
    VulnerabilitySummary
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard data aggregation.
    """

    @staticmethod
    async def _get_risk_counts(db: AsyncSession, user_id: int) -> Dict[str, int]:
        """Return counts for risk levels in a single grouped query."""
        result = await db.execute(
            select(Project.overall_risk_level, func.count(Project.id))
            .where(Project.user_id == user_id)
            .group_by(Project.overall_risk_level)
        )
        rows = result.all()
        counts = {"low": 0, "medium": 0, "high": 0}
        for level, count in rows:
            if level in counts:
                counts[level] = count or 0
        return counts

    @staticmethod
    async def get_dashboard_summary(
        db: AsyncSession,
        user_id: int,
    ) -> DashboardSummary:
        """Get dashboard summary statistics for a user."""
        # Total projects
        total_projects_result = await db.execute(
            select(func.count(Project.id)).where(Project.user_id == user_id)
        )
        total_projects = total_projects_result.scalar() or 0

        # Total analyzed projects (last_analyzed_at IS NOT NULL)
        total_analyzed_result = await db.execute(
            select(func.count(Project.id)).where(
                and_(
                    Project.user_id == user_id,
                    Project.last_analyzed_at.isnot(None),
                )
            )
        )
        total_analyzed = total_analyzed_result.scalar() or 0

        # Risk counts (single grouped query)
        risk_counts = await DashboardService._get_risk_counts(db, user_id)
        low_risk_count = risk_counts["low"]
        medium_risk_count = risk_counts["medium"]
        high_risk_count = risk_counts["high"]

        # Vulnerability totals across analyses of user's projects
        # Use COALESCE to get a single-row result with zeros when no data.
        vuln_result = await db.execute(
            select(
                func.coalesce(func.sum(Analysis.vulnerability_count), 0),
                func.coalesce(func.sum(Analysis.critical_vulnerabilities), 0),
            )
            .join(Project, Project.id == Analysis.project_id)
            .where(Project.user_id == user_id)
        )
        vuln_row = vuln_result.first() or (0, 0)
        total_vulns = vuln_row[0] or 0
        critical_vulns = vuln_row[1] or 0

        # Recent analyses in the last 7 days
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_analyses_result = await db.execute(
            select(func.count(Analysis.id))
            .join(Project, Project.id == Analysis.project_id)
            .where(
                and_(
                    Project.user_id == user_id,
                    Analysis.analyzed_at >= seven_days_ago,
                )
            )
        )
        recent_analyses = recent_analyses_result.scalar() or 0

        return DashboardSummary(
            total_projects=total_projects,
            total_analyzed=total_analyzed,
            low_risk_count=low_risk_count,
            medium_risk_count=medium_risk_count,
            high_risk_count=high_risk_count,
            total_vulnerabilities=total_vulns,
            critical_vulnerabilities=critical_vulns,
            recent_analyses=recent_analyses,
        )

    @staticmethod
    async def get_project_timeline(
        db: AsyncSession,
        project_id: int,
        user_id: int,
    ) -> ProjectScoreHistory:
        """Get historical score data for a project.

        Raises:
            ValueError: if project not found or not owned by user.
        """
        project_result = await db.execute(
            select(Project).where(
                and_(Project.id == project_id, Project.user_id == user_id)
            )
        )
        project = project_result.scalar_one_or_none()

        if not project:
            logger.debug("get_project_timeline: project %s not found for user %s", project_id, user_id)
            raise ValueError("Project not found")

        analyses_result = await db.execute(
            select(Analysis)
            .where(Analysis.project_id == project_id)
            .order_by(Analysis.analyzed_at.asc())
        )
        analyses = analyses_result.scalars().all()

        timeline: List[TimelineDataPoint] = []
        for analysis in analyses:
            timeline.append(
                {
                    "date": analysis.analyzed_at.isoformat(),
                    "maintenance_score": analysis.maintenance_score,
                    "activity_score": analysis.activity_score,
                    "security_score": analysis.security_score,
                    "vulnerability_count": analysis.vulnerability_count,
                }
            )

        return ProjectScoreHistory(
            project_id=project.id,
            project_name=project.name,
            timeline=timeline,
        )

    @staticmethod
    async def get_vulnerabilities_summary(
        db: AsyncSession, user_id: int
    ) -> List[VulnerabilitySummary]:
        """Get vulnerability summary for all user projects.

        Fetch latest analysis per project using a correlated subquery to avoid
        client-side deduplication and to include projects without analyses.
        Attempts to read medium/low if the Analysis model exposes those columns.
        """
        start = datetime.now(timezone.utc)

        # Correlated subquery that returns the latest Analysis.id for each Project.
        # Note: call correlate(Project) so SQLAlchemy knows this subquery depends on Project.
        latest_analysis_id_sq = (
            select(Analysis.id)
            .where(Analysis.project_id == Project.id)
            .order_by(Analysis.analyzed_at.desc())
            .limit(1)
            .correlate(Project)
            .scalar_subquery()
        )

        result = await db.execute(
            select(Project, Analysis)
            .outerjoin(Analysis, Analysis.id == latest_analysis_id_sq)
            .where(Project.user_id == user_id)
            .order_by(Project.name)
        )

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        logger.debug("get_vulnerabilities_summary executed in %.3fs for user %s", elapsed, user_id)

        rows = result.all()
        summaries: List[VulnerabilitySummary] = []
        for project, analysis in rows:
            if analysis is not None:
                # Safely read optional columns if present on model
                medium = getattr(analysis, "medium_vulnerabilities", 0) or 0
                low = getattr(analysis, "low_vulnerabilities", 0) or 0

                summaries.append(
                    VulnerabilitySummary(
                        project_id=project.id,
                        project_name=project.name,
                        total_vulnerabilities=analysis.vulnerability_count or 0,
                        critical=analysis.critical_vulnerabilities or 0,
                        high=analysis.high_vulnerabilities or 0,
                        medium=medium,
                        low=low,
                        last_checked=analysis.analyzed_at,
                    )
                )
            else:
                # Project has no analyses yet
                summaries.append(
                    VulnerabilitySummary(
                        project_id=project.id,
                        project_name=project.name,
                        total_vulnerabilities=0,
                        critical=0,
                        high=0,
                        medium=0,
                        low=0,
                        last_checked=None,
                    )
                )

        return summaries
