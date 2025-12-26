import httpx
from app.core.config import settings
from app.schemas.auth import GitHubUser

class GitHubOAuthService:
    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_API_URL = "https://api.github.com/user"

    @staticmethod
    def get_authorization_url(state: str) -> str:
        """Generate GitHub OAuth authorization URL"""
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_CALLBACK_URL,
            "scope": "read:user user:email",
            "state": state
        }
        query = "&".join([f"{k}={v}" for k,v in params.items()])
        return f"{GitHubOAuthService.AUTHORIZE_URL}?{query}"

    @staticmethod
    async def exchange_code_for_tokem(code: str) -> str | None:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GitHubOAuthService.ACCESS_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "redirect_url": settings.GITHUB_CALLBACK_URL,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            return None

    @staticmethod
    async def get_user_info(access_token: str) -> GitHubUser | None:
        """Get user information from GitHub API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GitHubOAuthService.USER_API_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )

            if response.status_code == 200:
                data = response.json()
                return GitHubUser(
                    id=data["id"],
                    login=data["login"],
                    email=data.get("email"),
                    name=data.get("name"),
                )
            return None