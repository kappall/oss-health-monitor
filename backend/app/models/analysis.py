from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Maintenance metrics
    commit_frequency = Column(Float, nullable=True)
    contributor_count = Column(Integer, nullable=True)
    last_commit_date = Column(DateTime, nullable=True)
    
    # Activity metrics
    issue_count = Column(Integer, nullable=True)
    average_issue_response_time = Column(Float, nullable=True)  # in hours
    release_frequency = Column(Float, nullable=True)
    
    # Security metrics
    vulnerability_count = Column(Integer, default=0)
    critical_vulnerabilities = Column(Integer, default=0)
    high_vulnerabilities = Column(Integer, default=0)
    
    # Scores
    maintenance_score = Column(Float, nullable=True)  # 0-100
    activity_score = Column(Float, nullable=True)    # 0-100
    security_score = Column(Float, nullable=True)    # 0-100
    overall_risk_level = Column(String(50), nullable=True)  # "low", "medium", "high"
    
    # Raw data storage
    raw_data = Column(JSON, nullable=True)
    
    analyzed_at = Column(DateTime(), default=datetime.now(timezone.utc))
    created_at = Column(DateTime(), default=datetime.now(timezone.utc))

    project = relationship("Project", back_populates="analyses")
