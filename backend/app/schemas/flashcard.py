"""
Pydantic schemas for Flashcard API requests and responses.
Senior Tip: Separate schemas for create, review, and response.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Literal


# ============================================================================
# Request Schemas
# ============================================================================

class FlashcardCreate(BaseModel):
    """Create flashcard from AI-generated data or manually."""
    document_id: Optional[int] = None
    question: str = Field(..., min_length=1, max_length=1000)
    answer: str = Field(..., min_length=1, max_length=2000)
    context: Optional[str] = None
    difficulty_level: Literal["easy", "medium", "hard"] = "medium"


class FlashcardUpdate(BaseModel):
    """Update flashcard content."""
    question: Optional[str] = None
    answer: Optional[str] = None
    context: Optional[str] = None


class FlashcardReview(BaseModel):

    quality: Literal["again", "hard", "good", "easy"]
   

class BulkFlashcardCreate(BaseModel):
    """Create multiple flashcards at once (from AI generation)."""
    document_id: int
    flashcards: List[FlashcardCreate]


class FlashcardResponse(BaseModel):
    """Standard flashcard response."""
    id: int
    user_id: int
    document_id: Optional[int]
    question: str
    answer: str
    context: Optional[str]
    difficulty_level: str
    
    # Spaced repetition data
    repetitions: int
    easiness_factor: float
    interval: int
    next_review_date: datetime
    
    # Performance
    total_reviews: int
    correct_reviews: int
    accuracy: float  # Calculated property
    
    # Metadata
    created_at: datetime
    last_reviewed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class FlashcardWithSource(FlashcardResponse):
    """Flashcard with document info."""
    document_title: Optional[str] = None
    document_filename: Optional[str] = None


class ReviewResult(BaseModel):
    """Result after reviewing a flashcard."""
    flashcard_id: int
    quality: str
    next_review_date: datetime
    interval_days: int
    is_correct: bool
    new_repetitions: int
    new_easiness_factor: float


class DueFlashcardsResponse(BaseModel):
    """Flashcards due for review."""
    due_cards: List[FlashcardResponse]
    total_due: int
    new_cards: int
    review_cards: int


class StudySessionSummary(BaseModel):
    """Summary after study session."""
    session_id: int
    cards_reviewed: int
    cards_correct: int
    cards_incorrect: int
    accuracy: float
    duration_seconds: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True