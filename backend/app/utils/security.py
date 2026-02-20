from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings


class SecurityManager:


    def __init__(self):
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # Pre-computed to maintain constant-time response on login failures,
        # preventing timing-based user enumeration attacks.
        self._dummy_hash = self._pwd_context.hash("dummy-timing-placeholder")

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self._pwd_context.verify(plain_password, hashed_password)

    def get_dummy_hash(self) -> str:
        """Return pre-computed dummy hash for constant-time login responses."""
        return self._dummy_hash

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = data.copy()
        expire = (
            datetime.now() + expires_delta
            if expires_delta
            else datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def decode_access_token(self, token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError:
            return None


# Module-level singleton
security_manager = SecurityManager()


hash_password = security_manager.hash_password
verify_password = security_manager.verify_password
create_access_token = security_manager.create_access_token
decode_access_token = security_manager.decode_access_token
DUMMY_HASH = security_manager.get_dummy_hash()
