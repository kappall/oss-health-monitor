from pydantic import BaseModel, HttpUrl, field_validator
from datetime import datetime
from app.models.project import ProjectType
from urllib.parse import urlparse

class ProjectSubmit(BaseModel):
    repository_url: str

    @field_validator('repository_url')
    @classmethod
    def validate_repository_url(cls, v: str) -> str:
        v = v.strip().strip('<>')
        if not v:
            raise ValueError("repository_url is empty")

        if v.startswith('npm:'):
            pkg = v[len('npm:'):].strip()
            if not pkg:
                raise ValueError("Invalid npm package name")
            return f"npm:{pkg}"

        if v.startswith('pypi:'):
            pkg = v[len('pypi:'):].strip()
            if not pkg:
                raise ValueError("Invalid pypi package name")
            return f"pypi:{pkg}"

        parsed = urlparse(v if v.startswith(('http://', 'https://')) else f"https://{v}")

        if parsed.netloc.lower() in ("github.com", "www.github.com"):
            path_parts = [p for p in parsed.path.strip("/").split("/") if p]
            if len(path_parts) < 2:
                raise ValueError("GitHub URL must include owner and repo (owner/repo)")
            owner, repo = path_parts[0], path_parts[1]
            return f"https://github.com/{owner}/{repo}"

        if "/" in v and " " not in v:
            parts = [p for p in v.strip("/").split("/") if p]
            if len(parts) >= 2:
                return f"https://github.com/{parts[0]}/{parts[1]}"

        raise ValueError(
            "Invalid repository URL. Use format: https://github.com/owner/repo, owner/repo, npm:package-name, or pypi:package-name"
        )
    
class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    repository_url: str
    project_type: ProjectType

class ProjectUpdate(BaseModel):
    description: str | None = None

class ProjectResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: str | None = None
    repository_url: str
    project_type: ProjectType
    maintenance_score: float | None = None
    activity_score: float | None = None
    security_score: float | None = None
    overall_risk_level: str | None = None
    last_analyzed_at: datetime | None = None
    favorites_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int
    page: int
    page_size: int