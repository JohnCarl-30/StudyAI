from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Flashcard(Base):
    __tablename__ = "flashcards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    difficulty_level = Column(String, default="medium")
    
    # Spaced repetition
    repetitions = Column(Integer, default=0)
    easiness_factor = Column(Float, default=2.5)
    interval = Column(Integer, default=1)
    next_review_date = Column(DateTime, default=datetime.utcnow)
    total_reviews = Column(Integer, default=0)
    correct_reviews = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_reviewed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="flashcards")  # ← matches User.flashcards
    document = relationship("Document", back_populates="flashcards")  # ← matches Document.flashcards
    
    @property
    def accuracy(self) -> float:
        if self.total_reviews == 0:
            return 0.0
        return (self.correct_reviews / self.total_reviews) * 100
    
    @property
    def is_due(self) -> bool:
        return datetime.now() >= self.next_review_date
    
    def __repr__(self):
        return f"<Flashcard {self.id}>"