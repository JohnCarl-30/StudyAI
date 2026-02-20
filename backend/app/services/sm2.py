"""
SM-2 Spaced Repetition Algorithm

Quality ratings (matches Anki's scale):
  "again" -> 0  Card was completely wrong, reset
  "hard"  -> 2  Correct but very difficult
  "good"  -> 4  Correct with some hesitation
  "easy"  -> 5  Correct with no hesitation
"""
from datetime import datetime, timedelta
from dataclasses import dataclass

QUALITY_MAP = {
    "again": 0,
    "hard": 2,
    "good": 4,
    "easy": 5,
}

MIN_EASINESS = 1.3


@dataclass
class SM2Result:
    repetitions: int
    easiness_factor: float
    interval: int          # days until next review
    next_review_date: datetime
    is_correct: bool


def calculate_sm2(
    quality: str,
    repetitions: int,
    easiness_factor: float,
    interval: int,
) -> SM2Result:
    
    q = QUALITY_MAP[quality]
    is_correct = q >= 3

    if not is_correct:
        # Incorrect — reset streak, review again soon
        new_repetitions = 0
        new_interval = 1
        new_ef = easiness_factor  # EF unchanged on failure in classic SM-2
    else:
        new_repetitions = repetitions + 1

        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            new_interval = round(interval * easiness_factor)

        # Update easiness factor
        new_ef = easiness_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = max(MIN_EASINESS, new_ef)

    next_review = datetime.utcnow() + timedelta(days=new_interval)

    return SM2Result(
        repetitions=new_repetitions,
        easiness_factor=round(new_ef, 4),
        interval=new_interval,
        next_review_date=next_review,
        is_correct=is_correct,
    )
