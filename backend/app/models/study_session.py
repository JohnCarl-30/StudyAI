from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class StudySession(Base):
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    cards_reviewed = Column(Integer, default=0)
    cards_correct = Column(Integer, default=0)
    cards_incorrect = Column(Integer, default=0)
    duration_seconds = Column(Integer, nullable=True)
    session_type = Column(String, default="review")
    
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="study_sessions") 
    
    @property
    def accuracy(self) -> float:
        if self.cards_reviewed == 0:
            return 0.0
        return (self.cards_correct / self.cards_reviewed) * 100
    
    def __repr__(self):
        return f"<StudySession {self.id}>"
