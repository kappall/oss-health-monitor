from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
import enum

class ProjectType(str, enum.Enum):
    GITHUB_REPO = "github_repo"
    NPM_PACKAGE = "npm_package"
    PYPI_PACKAGE = "pypi_package"

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    repository_url = Column(String(500), unique=True, index=True, nullable=False)
    project_type = Column(Enum(ProjectType), default=ProjectType.GITHUB_REPO)
    
    # Risk scores
    maintenance_score = Column(Float, nullable=True)
    activity_score = Column(Float, nullable=True)
    security_score = Column(Float, nullable=True)
    overall_risk_level = Column(String(50), nullable=True)  # "low", "medium", "high"
    
    # Metadata
    last_analyzed_at = Column(DateTime, nullable=True)
    is_favorited = Column(Integer, default=0)  # Count of favorites
    created_at = Column(DateTime, default=datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(datetime.timezone.utc), onupdate=datetime.now(datetime.timezone.utc))

    user = relationship("User", back_populates="projects")
    analyses = relationship("Analysis", back_populates="project", cascade="all, delete-orphan")
    vulnerabilities = relationship("Vulnerability", back_populates="project", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="project", cascade="all, delete-orphan")
