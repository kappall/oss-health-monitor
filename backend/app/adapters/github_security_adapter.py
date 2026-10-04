import logging
import asyncio
import httpx
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class GitHubSecurityAdapter:
    """Adapter for GitHub Security Advisories API"""

    BASE_URL = "https://api.github.com"
    DEFAULT_TIMEOUT = getattr(settings, "HTTP_TIMEOUT", 10.0)
    DEFAULT_RETRIES = getattr(settings, "HTTP_MAX_RETRIES", 3)
    PER_PAGE = getattr(settings, "GITHUB_PER_PAGE", 100)

    def __init__(self, access_token: str | None = None):
        self.access_token = access_token or getattr(settings, "GITHUB_API_TOKEN", None)
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "oss-health-monitor",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"

        self.client = httpx.AsyncClient(base_url=self.BASE_URL, headers=self.headers, timeout=self.DEFAULT_TIMEOUT)

    async def aclose(self) -> None:
        await self.client.aclose()

    async def _request(self, method: str, path: str, params: dict | None = None, **kwargs) -> httpx.Response | None:
        backoff = 1.0
        url = path
        for _ in range(self.DEFAULT_RETRIES):
            try:
                resp = await self.client.request(method, url, params=params, **kwargs)
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status in (429, 502, 503, 504):
                    logger.warning("Transient GitHub Security API status %s for %s %s, retrying after %s", status, method, url, backoff)
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                logger.exception("GitHub Security API returned error %s for %s %s", status, method, url)
                return None
            except httpx.RequestError:
                logger.exception("Network error when calling GitHub Security API %s %s, retrying after %s", method, url, backoff)
                await asyncio.sleep(backoff)
                backoff *= 2
                continue
        logger.error("Max retries exceeded for %s %s", method, url)
        return None

    async def get_repository_advisories(
        self,
        owner: str,
        repo: str
    ) -> List[Dict[str, Any]]:
        """Get security advisories for a repository"""
        resp = await self._request("GET", f"/repos/{owner}/{repo}/security-advisories", params={"per_page": self.PER_PAGE})
        if not resp:
            return []
        try:
            return resp.json() or []
        except Exception:
            logger.exception("Failed to parse advisories response for %s/%s", owner, repo)
            return []

    async def get_repository_dependabot_alerts(
        self,
        owner: str,
        repo: str
    ) -> List[Dict[str, Any]]:
        """Get Dependabot alerts for a repository"""
        resp = await self._request("GET", f"/repos/{owner}/{repo}/dependabot/alerts", params={"per_page": self.PER_PAGE, "state": "open"})
        if not resp:
            return []
        try:
            return resp.json() or []
        except Exception:
            logger.exception("Failed to parse dependabot alerts for %s/%s", owner, repo)
            return []
