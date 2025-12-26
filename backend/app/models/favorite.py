from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(datetime.timezone.utc))

    # Ensure user can only favorite a project once
    __table_args__ = (UniqueConstraint('user_id', 'project_id', name='_user_project_uc'),)

    user = relationship("User", back_populates="favorites")
    project = relationship("Project", back_populates="favorites")
