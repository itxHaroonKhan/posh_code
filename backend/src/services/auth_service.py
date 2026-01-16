from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlmodel import Session, select

from ..models import User, UserCreate, UserRead
from ..config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user_id: int, email: str) -> str:
        expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRY_DAYS)
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "exp": expire
        }
        return jwt.encode(
            to_encode,
            settings.BETTER_AUTH_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(
                token,
                settings.BETTER_AUTH_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            return None

    @staticmethod
    def register_user(session: Session, user_data: UserCreate) -> User:
        existing_user = session.exec(
            select(User).where(User.email == user_data.email)
        ).first()

        if existing_user:
            raise ValueError("Email already registered")

        user = User(
            email=user_data.email,
            password_hash=AuthService.hash_password(user_data.password)
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @staticmethod
    def authenticate_user(
        session: Session, email: str, password: str
    ) -> Optional[User]:
        user = session.exec(
            select(User).where(User.email == email)
        ).first()

        if not user:
            return None

        if not AuthService.verify_password(password, user.password_hash):
            return None

        return user

    @staticmethod
    def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
        return session.get(User, user_id)
