import asyncio
import logging
import re
from typing import Dict, Any, Tuple

import httpx
from datetime import datetime
from urllib.parse import urlparse

from app.core.config import settings

logger = logging.getLogger(__name__)


class GitHubAdapter:
    """Adapter for GitHub API interactions"""

    BASE_URL = "https://api.github.com"
    DEFAULT_TIMEOUT = getattr(settings, "HTTP_TIMEOUT", 10.0)
    DEFAULT_RETRIES = getattr(settings, "HTTP_MAX_RETRIES", 3)
    PER_PAGE = getattr(settings, "GITHUB_PER_PAGE", 100)

    def __init__(self, access_token: str | None = None):
        self.access_token = access_token or settings.GITHUB_API_TOKEN
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "oss-health-monitor",
            "X-Github-Api-Version": "2022-11-28",
        }
        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"

        self.client = httpx.AsyncClient(headers=self.headers, timeout=self.DEFAULT_TIMEOUT)

    async def aclose(self) -> None:
        await self.client.aclose()

    async def _request(self, method: str, path: str, params: dict | None = None, **kwargs) -> httpx.Response | None:
        url = f"{self.BASE_URL}{path}"
        backoff = 1.0
        for _ in range(self.DEFAULT_RETRIES):
            try:
                resp = await self.client.request(method, url, params=params, **kwargs)
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status in (429, 502, 503, 504):
                    logger.warning("Transient GitHub API status %s for %s %s, retrying after %s", status, method, url, backoff)
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                logger.exception("GitHub API returned error %s for %s %s", status, method, url)
                return None
            except httpx.RequestError:
                logger.exception("Network error when calling GitHub API %s %s, retrying after %s", method, url, backoff)
                await asyncio.sleep(backoff)
                backoff *= 2
                continue
        logger.error("Max retries exceeded for %s %s", method, url)
        return None

    def _extract_total_from_link(self, link_header: str) -> int | None:
        if not link_header:
            return None
        match = re.search(r'page=(\d+)>;\s*rel="last"', link_header)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    async def _get_total_count(self, path: str, params: dict | None = None) -> int:
        params = dict(params or {})
        params.update({"per_page": 1})
        resp = await self._request("GET", path, params=params)
        if not resp:
            return 0
        link = resp.headers.get("Link", "")
        total_pages = self._extract_total_from_link(link)
        if total_pages is not None:
            return total_pages
        # fallback: number of items returned (small repos / single page)
        return len(resp.json() or [])

    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any] | None:
        resp = await self._request("GET", f"/repos/{owner}/{repo}")
        if resp:
            return resp.json()
        return None

    async def get_commit_activity(self, owner: str, repo: str) -> Dict[str, Any] | None:
        commit_count = await self._get_total_count(f"/repos/{owner}/{repo}/commits")
        # fetch latest 10 commits for analysis
        resp = await self._request("GET", f"/repos/{owner}/{repo}/commits", params={"per_page": 10})
        commits = resp.json() if resp else []
        return {
            "commit_count": commit_count,
            "commits": commits[:10]
        }

    async def get_contributors(self, owner: str, repo: str) -> int:
        return await self._get_total_count(f"/repos/{owner}/{repo}/contributors", params={"anon": "true"})

    async def get_issues_stats(self, owner: str, repo: str) -> Dict[str, Any] | None:
        open_count = await self._get_total_count(f"/repos/{owner}/{repo}/issues", params={"state": "open"})
        resp = await self._request("GET", f"/repos/{owner}/{repo}/issues", params={"state": "open", "per_page": 5})
        issues = resp.json() if resp else []
        return {
            "open_count": open_count,
            "issues": issues[:5]
        }

    async def get_releases(self, owner: str, repo: str) -> Dict[str, Any] | None:
        resp = await self._request("GET", f"/repos/{owner}/{repo}/releases", params={"per_page": 10})
        if resp:
            releases = resp.json() or []
            return {
                "release_count": len(releases),
                "latest_release": releases[0] if releases else None,
                "releases": releases
            }
        return None

    @staticmethod
    def parse_github_url(url: str) -> Tuple[str, str] | None:
        """Parse GitHub URL to extract owner and repo"""
        try:
            u = url.strip().strip("<>").rstrip("/").replace(".git", "")
            if not u.startswith(("http://", "https://")):
                u = f"https://{u}"
            parsed = urlparse(u)
            if parsed.netloc.lower().endswith("github.com"):
                parts = [p for p in parsed.path.strip("/").split("/") if p]
                if len(parts) >= 2:
                    return parts[0], parts[1]
            # fallback: owner/repo plain string
            if "/" in url and " " not in url:
                parts = [p for p in url.strip("/").split("/") if p]
                if len(parts) >= 2:
                    return parts[0], parts[1]
            return None
        except Exception:
            logger.exception("Failed to parse GitHub URL: %s", url)
            return None