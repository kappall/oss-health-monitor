import asyncio
import logging
from typing import List, Dict, Any

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class OSVAdapter:
    """Adapter for OSV.dev API - Open Source Vulnerabilities"""

    BASE_URL = getattr(settings, "OSV_API_URL", "https://api.osv.dev")
    DEFAULT_TIMEOUT = getattr(settings, "HTTP_TIMEOUT", 10.0)
    DEFAULT_RETRIES = getattr(settings, "HTTP_MAX_RETRIES", 3)

    def __init__(self):
        self.base_url = self.BASE_URL
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "oss-health-monitor",
        }
        self.client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=self.DEFAULT_TIMEOUT)

    async def aclose(self) -> None:
        await self.client.aclose()

    async def _request(self, method: str, path: str, params: dict | None = None, json: dict | None = None, **kwargs) -> httpx.Response | None:
        backoff = 1.0
        url = path
        for _ in range(self.DEFAULT_RETRIES):
            try:
                resp = await self.client.request(method, url, params=params, json=json, **kwargs)
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status in (429, 502, 503, 504):
                    logger.warning("Transient OSV API status %s for %s %s, retrying after %s", status, method, url, backoff)
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                logger.exception("OSV API returned error %s for %s %s", status, method, url)
                return None
            except httpx.RequestError:
                logger.exception("Network error when calling OSV API %s %s, retrying after %s", method, url, backoff)
                await asyncio.sleep(backoff)
                backoff *= 2
                continue
        logger.error("Max retries exceeded for %s %s", method, url)
        return None

    async def query_vulnerabilities(
        self,
        package_name: str,
        version: str | None = None,
        ecosystem: str = "PyPI"  # PyPI, npm, etc.
    ) -> List[Dict[str, Any]]:
        """Query OSV for vulnerabilities in a package"""
        payload: Dict[str, Any] = {
            "package": {"name": package_name, "ecosystem": ecosystem}
        }
        if version:
            payload["version"] = version

        resp = await self._request("POST", "/v1/query", json=payload)
        if not resp:
            return []
        try:
            data = resp.json()
            return data.get("vulns", []) or []
        except Exception:
            logger.exception("Failed to parse OSV response for %s %s", package_name, version)
            return []

    async def get_vulnerability_details(
        self,
        vuln_id: str
    ) -> Dict[str, Any] | None:
        """Get detailed information about a specific vulnerability"""
        resp = await self._request("GET", f"/v1/vulns/{vuln_id}")
        if not resp:
            return None
        try:
            return resp.json()
        except Exception:
            logger.exception("Failed to parse OSV vuln details for %s", vuln_id)
            return None