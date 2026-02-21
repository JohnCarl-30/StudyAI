from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    title = Column(String, nullable=True)
    page_count = Column(Integer, nullable=True)
    
    status = Column(Enum(ProcessingStatus, values_callable=lambda x: [e.value for e in x]), default=ProcessingStatus.PENDING)
    processing_error = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="documents")  # ← matches User.documents
    flashcards = relationship("Flashcard", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document {self.filename}>"