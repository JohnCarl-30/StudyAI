"""
Pydantic schemas for Chat/Q&A requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QueryMode(str, Enum):
    
    NORMAL = "normal"           # Regular Q&A
    ELI5 = "eli5"              # Explain Like I'm 5
    PRACTICE = "practice"       # Generate practice problems
    SUMMARY = "summary"         # Summarize a topic
    GENERATE_FLASHCARDS = "generate_flashcards"  


class ChatMessage(BaseModel):
   
    role: str          # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    document_id: Optional[int] = None     
    query_mode: QueryMode = QueryMode.NORMAL
    chat_history: Optional[List[ChatMessage]] = []


class SourceDocument(BaseModel):
    content: str
    page: Optional[str]
    document_id: Optional[int]


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    query_mode: str


class GenerateFlashcardsRequest(BaseModel):
    document_id: int
    topic: Optional[str] = None          
    num_cards: int = Field(default=10, ge=1, le=30)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM        
    answer: str = Field(default="detailed")  
    
    


class SearchRequest(BaseModel):
   
    query: str = Field(..., min_length=1)
    document_id: Optional[int] = None
    k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
  
    content: str
    page: Optional[str]
    document_id: Optional[int]