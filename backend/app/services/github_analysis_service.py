from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project
from app.models.analysis import Analysis
from app.models.vulnerability import Vulnerability, SeverityLevel
from app.adapters.github_adapter import GitHubAdapter
from app.adapters.github_security_adapter import GitHubSecurityAdapter
from app.services.analysis_service import AnalysisScoreService
from datetime import datetime, timezone
import logging
import json

logger = logging.getLogger(__name__)


class GitHubAnalysisService:
    """Service for analyzing GitHub repositories"""
    
    @staticmethod
    async def analyze_repository(
        db: AsyncSession,
        project: Project,
        user_github_token: str
    ) -> Analysis:
        """Analyze a GitHub repository and create analysis record"""
        
        parsed = GitHubAdapter.parse_github_url(project.repository_url)
        if not parsed:
            raise ValueError("Invalid GitHub URL")
        owner, repo = parsed

        github_adapter = GitHubAdapter(user_github_token)
        security_adapter = GitHubSecurityAdapter(user_github_token)
        try:
            # fetch data from GitHub
            repo_info = await github_adapter.get_repository_info(owner, repo)
            commits_data = await github_adapter.get_commit_activity(owner, repo)
            contributor_count = await github_adapter.get_contributors(owner, repo)
            issues_data = await github_adapter.get_issues_stats(owner, repo)
            releases_data = await github_adapter.get_releases(owner, repo)
            advisories = await security_adapter.get_repository_advisories(owner, repo)
            dependabot_alerts = await security_adapter.get_repository_dependabot_alerts(owner, repo)
        finally:
            # ensure clients are closed to free resources
            await github_adapter.aclose()
            await security_adapter.aclose()

        commits = commits_data.get("commits", []) if commits_data else []
        releases = releases_data.get("releases", []) if releases_data else []
        issues = issues_data.get("issues", []) if issues_data else []

        # last commit date (aware)
        last_commit_date = None
        if commits:
            s = commits[0].get('commit', {}).get('committer', {}).get('date')
            if s:
                try:
                    last_commit_date = datetime.fromisoformat(s.replace('Z', '+00:00'))
                except Exception:
                    last_commit_date = None

        # days since last commit (use timezone-aware now)
        last_commit_days_ago = 999
        if last_commit_date:
            last_commit_days_ago = int((datetime.now(timezone.utc) - last_commit_date).days)

        commit_frequency = AnalysisScoreService.calculate_commit_frequency(commits)
        release_frequency = AnalysisScoreService.calculate_release_frequency(releases)

        # Count vulnerabilities
        def sev_of(item: dict) -> str:
            return (item.get("severity") or "").lower()

        critical_vulns = len([v for v in advisories if sev_of(v) == 'critical'])
        high_vulns = len([v for v in advisories if sev_of(v) == 'high'])
        medium_vulns = len([v for v in advisories if sev_of(v) in ('medium', 'moderate')])
        total_vulns = len(advisories) + len(dependabot_alerts)

        # Estimate average issue response time (hours) using created_at / updated_at when available
        response_hours_list = []
        for it in issues:
            created = it.get("created_at")
            updated = it.get("updated_at")
            if not created:
                continue
            try:
                c_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                u_dt = datetime.fromisoformat(updated.replace('Z', '+00:00')) if updated else c_dt
                if u_dt > c_dt:
                    hrs = (u_dt - c_dt).total_seconds() / 3600.0
                    response_hours_list.append(hrs)
            except Exception:
                continue
        average_issue_response_time = float(sum(response_hours_list) / len(response_hours_list)) if response_hours_list else 24.0

        # Calculate scores
        maintenance_score, _ = AnalysisScoreService.calculate_maintenance_score(
            contributor_count=contributor_count or 0,
            last_commit_days_ago=last_commit_days_ago,
            release_frequency=release_frequency
        )
        
        activity_score, _ = AnalysisScoreService.calculate_activity_score(
            issue_count=len(issues),
            average_issue_response_time=average_issue_response_time,
            commit_frequency=commit_frequency
        )
        
        security_score, _ = AnalysisScoreService.calculate_security_score(
            critical_vulnerabilities=critical_vulns,
            high_vulnerabilities=high_vulns,
            medium_vulnerabilities=medium_vulns,
            total_vulnerabilities=total_vulns
        )
        
        overall_risk_level = AnalysisScoreService.calculate_overall_risk_level(
            maintenance_score,
            activity_score,
            security_score
        )
        
        analysis = Analysis(
            project_id=project.id,
            commit_frequency=commit_frequency,
            contributor_count=contributor_count or 0,
            last_commit_date=last_commit_date,
            issue_count=len(issues),
            average_issue_response_time=average_issue_response_time,
            release_frequency=release_frequency,
            vulnerability_count=total_vulns,
            critical_vulnerabilities=critical_vulns,
            high_vulnerabilities=high_vulns,
            maintenance_score=maintenance_score,
            activity_score=activity_score,
            security_score=security_score,
            overall_risk_level=overall_risk_level,
            analyzed_at=datetime.now(timezone.utc),
            raw_data={
                "repo_info": repo_info,
                "commits_count": commits_data.get("commit_count") if commits_data else 0,
                "releases_count": releases_data.get("release_count") if releases_data else 0,
                "issues_count": issues_data.get("open_count") if issues_data else 0,
                "advisories_count": len(advisories),
                "dependabot_alerts_count": len(dependabot_alerts),
            }
        )
        
        db.add(analysis)
        
        # update project with scores and last analyzed timestamp (tz-aware)
        project.maintenance_score = maintenance_score
        project.activity_score = activity_score
        project.security_score = security_score
        project.overall_risk_level = overall_risk_level
        project.last_analyzed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(analysis)
        await db.refresh(project)
        
        return analysis
