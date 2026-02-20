from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ProcessingStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUpload(BaseModel):
    title: Optional[str] = None
    
class DocumentUpdate(BaseModel):
    title: Optional[str] = None

class DocumentResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    title: Optional[str] = None
    file_size: int
    page_count: Optional[int]
    status: ProcessingStatusEnum
    processing_error: Optional[str]
    chunk_count: int
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class DocumentWithContent(DocumentResponse):
    extracted_text: Optional[str]

class DocumentList(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int

class ChunkCreate(BaseModel):
    document_id : int
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    
class ChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True