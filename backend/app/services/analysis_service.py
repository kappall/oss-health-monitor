from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class AnalysisScoreService:
    """Service for calculating risk scores and analysis"""

    @staticmethod
    def calculate_maintenance_score(
        contributor_count: int,
        last_commit_days_ago: int,
        release_frequency: float,
    ) -> Tuple[float, str]:
        """
        Calculate maintenance score (0-100) with per-parameter breakdown

        Contributors: up to 40 points
        Last commit recency: up to 35 points
        Releases per year: up to 25 points
        """
        # Contributors (0-40)
        if contributor_count >= 50:
            contrib_points = 40
            contrib_desc = "Very large contributor base"
        elif contributor_count >= 20:
            contrib_points = 30
            contrib_desc = "Healthy number of contributors"
        elif contributor_count >= 5:
            contrib_points = 20
            contrib_desc = "Small active team"
        elif contributor_count > 0:
            contrib_points = 10
            contrib_desc = "Very few contributors"
        else:
            contrib_points = 0
            contrib_desc = "No contributors"

        # Last commit recency (0-35)
        if last_commit_days_ago <= 7:
            recency_points = 35
            recency_desc = "Very recently updated"
        elif last_commit_days_ago <= 30:
            recency_points = 25
            recency_desc = "Recently updated"
        elif last_commit_days_ago <= 90:
            recency_points = 15
            recency_desc = "Occasionally updated"
        elif last_commit_days_ago <= 180:
            recency_points = 5
            recency_desc = "Infrequent updates"
        else:
            recency_points = 0
            recency_desc = "Likely unmaintained"

        # Releases per year (0-25)
        if release_frequency >= 12:
            release_points = 25
            release_desc = "Very frequent releases"
        elif release_frequency >= 4:
            release_points = 20
            release_desc = "Regular releases"
        elif release_frequency >= 1:
            release_points = 10
            release_desc = "Occasional releases"
        else:
            release_points = 0
            release_desc = "No recent releases"

        score = contrib_points + recency_points + release_points
        score = max(0, min(100, score))

        explanation = (
            f"Contributors: {contributor_count} -> {contrib_desc} (+{contrib_points}); "
            f"Last commit: {last_commit_days_ago} days -> {recency_desc} (+{recency_points}); "
            f"Releases/year: {release_frequency} -> {release_desc} (+{release_points})."
        )

        if score >= 80:
            overall = "Well-maintained project with active development"
        elif score >= 60:
            overall = "Moderately maintained with steady updates"
        elif score >= 40:
            overall = "Minimal maintenance activity"
        else:
            overall = "Poorly maintained or abandoned"

        explanation = f"{explanation} Summary: {overall}."
        return float(score), explanation

    @staticmethod
    def calculate_activity_score(
        issue_count: int,
        average_issue_response_time: float,
        commit_frequency: float,
    ) -> Tuple[float, str]:
        """
        Calculate activity score (0-100) with per-parameter breakdown

        Commit frequency: up to 40 points
        Issue response time: up to 35 points
        Issue volume: up to 25 points (moderate volume preferred)
        """
        # Commit frequency (0-40)
        if commit_frequency >= 10:
            commit_points = 40
            commit_desc = "Very frequent commits"
        elif commit_frequency >= 5:
            commit_points = 30
            commit_desc = "Frequent commits"
        elif commit_frequency >= 2:
            commit_points = 20
            commit_desc = "Occasional commits"
        elif commit_frequency > 0:
            commit_points = 10
            commit_desc = "Rare commits"
        else:
            commit_points = 0
            commit_desc = "No recent commits"

        # Issue response time (hours) (0-35): faster is better
        if average_issue_response_time <= 24:
            response_points = 35
            response_desc = "Excellent response time"
        elif average_issue_response_time <= 72:
            response_points = 25
            response_desc = "Good response time"
        elif average_issue_response_time <= 168:
            response_points = 15
            response_desc = "Slow response"
        elif average_issue_response_time <= 720:
            response_points = 5
            response_desc = "Very slow response"
        else:
            response_points = 0
            response_desc = "No meaningful issue response"

        # Issue volume (0-25): moderate volume is ideal
        if 5 <= issue_count <= 50:
            issue_points = 25
            issue_desc = "Healthy issue volume (engaged community)"
        elif issue_count == 0:
            issue_points = 15
            issue_desc = "No open issues (could indicate low usage or very stable)"
        elif issue_count < 5:
            issue_points = 20
            issue_desc = "Low issue volume (normal)"
        elif issue_count <= 100:
            issue_points = 10
            issue_desc = "High issue volume (may indicate problems)"
        else:
            issue_points = 5
            issue_desc = "Very high issue volume (likely problematic)"

        score = commit_points + response_points + issue_points
        score = max(0, min(100, score))

        explanation = (
            f"Commits/mo: {commit_frequency} -> {commit_desc} (+{commit_points}); "
            f"Issue response: {average_issue_response_time}h -> {response_desc} (+{response_points}); "
            f"Issue count: {issue_count} -> {issue_desc} (+{issue_points})."
        )

        if score >= 80:
            overall = "Highly active project with fast issue response"
        elif score >= 60:
            overall = "Moderately active with responsive maintainers"
        elif score >= 40:
            overall = "Some activity but slower response times"
        else:
            overall = "Low activity and engagement"

        explanation = f"{explanation} Summary: {overall}."
        return float(score), explanation

    @staticmethod
    def calculate_security_score(
        critical_vulnerabilities: int,
        high_vulnerabilities: int,
        medium_vulnerabilities: int,
        total_vulnerabilities: int,
    ) -> Tuple[float, str]:
        """
        Calculate security score (0-100) with clear severity breakdown

        Heavier penalties for more severe vulnerabilities.
        """
        score = 100
        # Penalty weights
        score -= critical_vulnerabilities * 30
        score -= high_vulnerabilities * 10
        score -= medium_vulnerabilities * 3

        score = max(0, score)

        # Build explanation
        explanation_parts = []
        explanation_parts.append(f"Critical: {critical_vulnerabilities} (penalty {critical_vulnerabilities * 30})")
        explanation_parts.append(f"High: {high_vulnerabilities} (penalty {high_vulnerabilities * 10})")
        explanation_parts.append(f"Medium: {medium_vulnerabilities} (penalty {medium_vulnerabilities * 3})")
        explanation_parts.append(f"Total vulns: {total_vulnerabilities}")

        if score >= 90:
            summary = "No known vulnerabilities or very few minor ones"
        elif score >= 70:
            summary = "Few vulnerabilities, mostly low severity"
        elif score >= 50:
            summary = "Some vulnerabilities present, including high severity"
        elif score >= 30:
            summary = "Multiple vulnerabilities including critical ones"
        else:
            summary = "Serious security concerns with critical vulnerabilities"

        explanation = "; ".join(explanation_parts) + f". Summary: {summary}."
        return float(score), explanation

    @staticmethod
    def calculate_overall_risk_level(
        maintenance_score: float,
        activity_score: float,
        security_score: float,
    ) -> str:
        """Determine overall risk level based on all scores"""
        weighted_score = (
            (security_score * 0.5) +
            (maintenance_score * 0.3) +
            (activity_score * 0.2)
        )

        if weighted_score >= 70:
            return "low"
        elif weighted_score >= 50:
            return "medium"
        else:
            return "high"

    @staticmethod
    def calculate_commit_frequency(
        commits: list,
        days_period: int = 90
    ) -> float:
        """Calculate commits per month in the given period (consider commits within the window)"""
        if not commits:
            return 0.0

        try:
            now = datetime.now(timezone.utc)
            commit_dates = []
            for commit in commits:
                if isinstance(commit, dict):
                    # common shape returned by GitHub API
                    commit_date_str = (
                        commit.get("commit", {})
                              .get("committer", {})
                              .get("date")
                    )
                else:
                    commit_date_str = None

                if not commit_date_str:
                    continue
                try:
                    dt = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))
                except Exception:
                    continue
                # keep only within the period
                if (now - dt).days <= days_period:
                    commit_dates.append(dt)

            if not commit_dates:
                return 0.0

            commit_dates.sort()
            oldest = commit_dates[0]
            newest = commit_dates[-1]
            days_span = max(1.0, (newest - oldest).total_seconds() / 86400.0)
            commits_per_day = len(commit_dates) / days_span
            commits_per_month = commits_per_day * 30.0
            return round(commits_per_month, 2)
        except Exception:
            logger.exception("Error calculating commit frequency")
            return 0.0

    @staticmethod
    def calculate_release_frequency(releases: list) -> float:
        """Calculate releases per year"""
        if not releases:
            return 0.0

        try:
            published_dates = []
            for release in releases:
                if isinstance(release, dict):
                    published_date_str = release.get("published_at") or release.get("created_at")
                else:
                    published_date_str = None

                if not published_date_str:
                    continue
                try:
                    dt = datetime.fromisoformat(published_date_str.replace("Z", "+00:00"))
                except Exception:
                    continue
                published_dates.append(dt)

            if not published_dates:
                return 0.0

            published_dates.sort()
            oldest = published_dates[0]
            newest = published_dates[-1]
            days_span = max(1.0, (newest - oldest).total_seconds() / 86400.0)
            years_span = max(1.0 / 365.0, days_span / 365.0)
            releases_per_year = len(published_dates) / years_span
            return round(releases_per_year, 2)
        except Exception:
            logger.exception("Error calculating release frequency")
            return float(len(releases))
