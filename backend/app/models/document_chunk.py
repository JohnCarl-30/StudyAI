from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class DocumentChunk(Base):
    
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    chunk_index = Column(Integer, nullable=False)  # Order of the chunk in the document
    page_number = Column(Integer, nullable=True)  
    content = Column(Text, nullable=False)  # Extracted text content of the chunk
    
    #embedding_id = Column(String, nullable=True)  # ID of the embedding vector in the vector store
    
    created_at = Column(DateTime, default=datetime.now)
    
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk id={self.id} document_id={self.document_id} chunk_index={self.chunk_index}>"
    