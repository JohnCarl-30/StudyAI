from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.flashcard import Flashcard
from app.models.study_session import StudySession
from app.models.user import User
from app.schemas.flashcard import (
    BulkFlashcardCreate,
    DueFlashcardsResponse,
    FlashcardCreate,
    FlashcardResponse,
    FlashcardReview,
    ReviewResult,
    StudySessionSummary,
)
from app.services.sm2 import calculate_sm2

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.post("/", response_model=FlashcardResponse, status_code=status.HTTP_201_CREATED)
def create_flashcard(
    data: FlashcardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = Flashcard(user_id=current_user.id, **data.model_dump())
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.post("/bulk", response_model=List[FlashcardResponse], status_code=status.HTTP_201_CREATED)
def bulk_create_flashcards(
    data: BulkFlashcardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cards = [
        Flashcard(user_id=current_user.id, **card.model_dump())
        for card in data.flashcards
    ]
    db.add_all(cards)
    db.commit()
    for card in cards:
        db.refresh(card)
    return cards


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[FlashcardResponse])
def list_flashcards(
    document_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Flashcard).filter(Flashcard.user_id == current_user.id)
    if document_id is not None:
        query = query.filter(Flashcard.document_id == document_id)
    return query.offset(skip).limit(min(limit, 200)).all()


@router.get("/due", response_model=DueFlashcardsResponse)
def get_due_flashcards(
    document_id: Optional[int] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    query = db.query(Flashcard).filter(Flashcard.user_id == current_user.id)
    if document_id is not None:
        query = query.filter(Flashcard.document_id == document_id)

    all_cards = query.all()
    due = [c for c in all_cards if c.next_review_date <= now]
    due = due[:limit]

    new_cards = sum(1 for c in due if c.total_reviews == 0)
    review_cards = len(due) - new_cards

    return DueFlashcardsResponse(
        due_cards=due,
        total_due=len(due),
        new_cards=new_cards,
        review_cards=review_cards,
    )


@router.get("/{flashcard_id}", response_model=FlashcardResponse)
def get_flashcard(
    flashcard_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = db.query(Flashcard).filter(
        Flashcard.id == flashcard_id,
        Flashcard.user_id == current_user.id,
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return card


# ---------------------------------------------------------------------------
# Review (applies SM-2)
# ---------------------------------------------------------------------------

@router.post("/{flashcard_id}/review", response_model=ReviewResult)
def review_flashcard(
    flashcard_id: int,
    review: FlashcardReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = db.query(Flashcard).filter(
        Flashcard.id == flashcard_id,
        Flashcard.user_id == current_user.id,
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    result = calculate_sm2(
        quality=review.quality,
        repetitions=card.repetitions,
        easiness_factor=card.easiness_factor,
        interval=card.interval,
    )

    card.repetitions = result.repetitions
    card.easiness_factor = result.easiness_factor
    card.interval = result.interval
    card.next_review_date = result.next_review_date
    card.total_reviews += 1
    card.last_reviewed_at = datetime.utcnow()

    if result.is_correct:
        card.correct_reviews += 1

    db.commit()
    db.refresh(card)

    return ReviewResult(
        flashcard_id=card.id,
        quality=review.quality,
        next_review_date=result.next_review_date,
        interval_days=result.interval,
        is_correct=result.is_correct,
        new_repetitions=result.repetitions,
        new_easiness_factor=result.easiness_factor,
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.delete("/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flashcard(
    flashcard_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = db.query(Flashcard).filter(
        Flashcard.id == flashcard_id,
        Flashcard.user_id == current_user.id,
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    db.delete(card)
    db.commit()


# ---------------------------------------------------------------------------
# Study Sessions
# ---------------------------------------------------------------------------

@router.post("/sessions/start")
def start_study_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = StudySession(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id, "started_at": session.started_at}


@router.post("/sessions/{session_id}/end", response_model=StudySessionSummary)
def end_study_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.utcnow()
    session.completed_at = now
    session.duration_seconds = int((now - session.started_at).total_seconds())
    db.commit()
    db.refresh(session)
    return session


@router.patch("/sessions/{session_id}/record")
def record_review_in_session(
    session_id: int,
    correct: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.cards_reviewed += 1
    if correct:
        session.cards_correct += 1
    else:
        session.cards_incorrect += 1

    db.commit()
    return {"cards_reviewed": session.cards_reviewed, "accuracy": session.accuracy}


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@router.get("/analytics/summary")
def get_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cards = db.query(Flashcard).filter(Flashcard.user_id == current_user.id).all()
    sessions = db.query(StudySession).filter(StudySession.user_id == current_user.id).all()

    total_cards = len(cards)
    total_reviews = sum(c.total_reviews for c in cards)
    total_correct = sum(c.correct_reviews for c in cards)
    now = datetime.utcnow()
    due_today = sum(1 for c in cards if c.next_review_date <= now)
    mastered = sum(1 for c in cards if c.repetitions >= 3 and c.easiness_factor >= 2.0)

    overall_accuracy = round((total_correct / total_reviews * 100), 1) if total_reviews else 0.0

    completed_sessions = [s for s in sessions if s.completed_at]
    avg_session_duration = (
        round(sum(s.duration_seconds for s in completed_sessions) / len(completed_sessions))
        if completed_sessions else 0
    )

    return {
        "total_cards": total_cards,
        "total_reviews": total_reviews,
        "overall_accuracy": overall_accuracy,
        "due_today": due_today,
        "mastered_cards": mastered,
        "total_sessions": len(sessions),
        "avg_session_duration_seconds": avg_session_duration,
    }
