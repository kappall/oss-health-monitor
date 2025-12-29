from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Maintenance metrics
    commit_frequency = Column(Float, nullable=True)
    contributor_count = Column(Integer, nullable=True)
    last_commit_date = Column(DateTime(timezone=True), nullable=True)
    
    # Activity metrics
    issue_count = Column(Integer, nullable=True)
    average_issue_response_time = Column(Float, nullable=True)  # in hours
    release_frequency = Column(Float, nullable=True)
    
    # Security metrics
    vulnerability_count = Column(Integer, default=0)
    critical_vulnerabilities = Column(Integer, default=0)
    high_vulnerabilities = Column(Integer, default=0)
    medium_vulnerabilities = Column(Integer, default=0)
    
    # Scores
    maintenance_score = Column(Float, nullable=True)
    activity_score = Column(Float, nullable=True)
    security_score = Column(Float, nullable=True)
    overall_risk_level = Column(String(50), nullable=True)

    # Timestamp when this analysis was performed
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Raw data storage
    raw_data = Column(JSON, nullable=True)
    
    # Convenience properties for response_model (Pydantic reads attributes)
    @property
    def metrics(self) -> dict:
        return {
            "commit_frequency": self.commit_frequency,
            "contributor_count": self.contributor_count,
            "last_commit_date": self.last_commit_date,
            "issue_count": self.issue_count,
            "average_issue_response_time": self.average_issue_response_time,
            "release_frequency": self.release_frequency,
            "vulnerability_count": self.vulnerability_count,
            "critical_vulnerabilities": self.critical_vulnerabilities,
            "high_vulnerabilities": self.high_vulnerabilities,
            "medium_vulnerabilities": getattr(self, "medium_vulnerabilities", None),
        }

    @property
    def scores(self) -> dict:
        return {
            "maintenance_score": self.maintenance_score,
            "activity_score": self.activity_score,
            "security_score": self.security_score,
            "overall_risk_level": self.overall_risk_level,
        }
    
    project = relationship("Project", back_populates="analyses")
