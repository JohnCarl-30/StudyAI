from functools import lru_cache
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token
from app.services.document_service import DocumentService
from app.services.rag_services import RAGService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials

    _401 = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise _401

    user_id: int = payload.get("user_id")
    if user_id is None:
        raise _401

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise _401

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    """Inject a DocumentService instance into route handlers."""
    return DocumentService(db)


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    """
    Return a cached RAGService singleton.
    RAGService.__init__ initialises LLM clients — caching avoids
    that overhead on every request.
    """
    return RAGService()
