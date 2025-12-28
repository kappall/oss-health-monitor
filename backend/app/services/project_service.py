from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.project import Project, ProjectType
from app.models.user import User
from app.schemas.project import ProjectSubmit, ProjectCreate
from app.adapters.github_adapter import GitHubAdapter

class ProjectService:
    """Service for project operations"""
    
    @staticmethod
    async def submit_project(
        db: AsyncSession,
        user: User,
        submission: ProjectSubmit
    ) -> Project:
        """Submit a new project for analysis"""
        
        repository_url = submission.repository_url
        project_type = ProjectType.GITHUB_REPO
        name = ""
        description = None
        
        if repository_url.startswith('npm:'):
            project_type = ProjectType.NPM_PACKAGE
            name = repository_url.replace('npm:', '')
        elif repository_url.startswith('pypi:'):
            project_type = ProjectType.PYPI_PACKAGE
            name = repository_url.replace('pypi:', '')
        elif 'github.com' in repository_url:
            github_adapter = GitHubAdapter(user.github_token)
            parsed = GitHubAdapter.parse_github_url(repository_url)
            
            if not parsed:
                raise ValueError("Invalid GitHub repository URL")
            
            owner, repo = parsed
            repo_info = await github_adapter.get_repository_info(owner, repo)
            
            if not repo_info:
                raise ValueError("Repository not found or not accessible")
            
            name = repo_info.get('full_name', f"{owner}/{repo}")
            description = repo_info.get('description')
        
        result = await db.execute(
            select(Project).where(
                Project.user_id == user.id,
                Project.repository_url == repository_url
            )
        )
        existing_project = result.scalar_one_or_none()
        
        if existing_project:
            return existing_project
        
        project = Project(
            user_id=user.id,
            name=name,
            description=description,
            repository_url=repository_url,
            project_type=project_type
        )
        
        db.add(project)
        await db.commit()
        await db.refresh(project)
        
        return project
    
    @staticmethod
    async def get_user_projects(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Project], int]:
        """Get all projects for a user with pagination"""
        
        count_result = await db.execute(
            select(func.count(Project.id)).where(Project.user_id == user_id)
        )
        total = count_result.scalar()
        
        result = await db.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        projects = result.scalars().all()
        
        return list(projects), total
    
    @staticmethod
    async def get_project_by_id(
        db: AsyncSession,
        project_id: int,
        user_id: int
    ) -> Project | None :
        """Get a specific project by ID for a user"""
        result = await db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_project(
        db: AsyncSession,
        project_id: int,
        user_id: int
    ) -> bool:
        """Delete a project"""
        project = await ProjectService.get_project_by_id(db, project_id, user_id)
        
        if not project:
            return False
        
        await db.delete(project)
        await db.commit()
        
        return True
