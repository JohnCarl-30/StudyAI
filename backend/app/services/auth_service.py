"""
Authentication service — all auth business logic lives here.
Routes delegate to this class and only handle HTTP concerns.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import security_manager


class AuthService:
    """
    Handles user registration, authentication, and token creation.
    Does not raise HTTPException — raises ValueError for business rule failures
    so that callers (routes) control the HTTP response.
    """

    def __init__(self, db: Session):
        self.db = db
        self._security = security_manager

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, user_data: UserCreate) -> User:
        """
        Register a new user.
        Raises ValueError if the email is already registered.
        """
        if self.get_user_by_email(user_data.email):
            raise ValueError("Email already registered")

        new_user = User(
            email=user_data.email,
            hashed_password=self._security.hash_password(user_data.password),
            full_name=user_data.full_name,
            is_active=True,
            is_verified=False,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Verify credentials with constant-time comparison to prevent
        timing-based user enumeration attacks.
        Returns the User on success, None on failure.
        """
        user = self.get_user_by_email(email)
        hash_to_check = user.hashed_password if user else self._security.get_dummy_hash()
        if not self._security.verify_password(password, hash_to_check):
            return None
        return user

    def create_token_for_user(self, user: User) -> str:
        return self._security.create_access_token(
            data={"user_id": user.id, "email": user.email}
        )
