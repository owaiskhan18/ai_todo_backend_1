# backend/crud/user.py
from sqlmodel import Session, select
from models.user import User
from schemas.auth import UserCreate
from typing import Optional
from passlib.context import CryptContext
from fastapi import HTTPException
import hashlib

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def sha256_prehash(password: str) -> str:
    """
    Pre-hash a password with SHA256 and return a hex string.
    Safe for bcrypt (any length password, including emojis/Unicode).
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt safely for any length.
    """
    prehashed = sha256_prehash(password)
    return pwd_context.hash(prehashed)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against the hashed password.
    """
    prehashed = sha256_prehash(plain_password)
    return pwd_context.verify(prehashed, hashed_password)

def get_user_by_email(session: Session, email: str) -> Optional[User]:
    """
    Retrieve a user by email.
    """
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def create_user(session: Session, user_create: UserCreate) -> User:
    """
    Create a new user with a hashed password.
    Raises HTTPException if password is too short.
    """
    # Optional: enforce minimum password length
    if len(user_create.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password too short. Minimum 6 characters required."
        )

    hashed_password = get_password_hash(user_create.password)
    db_user = User(email=user_create.email, hashed_password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
