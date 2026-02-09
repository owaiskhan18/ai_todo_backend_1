from sqlmodel import Session, select
from models.user import User
from schemas.auth import UserCreate
from typing import Optional
from passlib.context import CryptContext
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
import hashlib

# -------------------------------
# Password hashing context using bcrypt
# -------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------------
# Prehash password using SHA256
# -------------------------------
def sha256_prehash(password: str) -> str:
    """
    Pre-hash a password with SHA256 to avoid bcrypt 72-byte limit.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# -------------------------------
# Hash password safely for bcrypt
# -------------------------------
def get_password_hash(password: str) -> str:
    prehashed = sha256_prehash(password)
    return pwd_context.hash(prehashed)

# -------------------------------
# Verify password against hash
# -------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    prehashed = sha256_prehash(plain_password)
    return pwd_context.verify(prehashed, hashed_password)

# -------------------------------
# Get user by email
# -------------------------------
def get_user_by_email(session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

# -------------------------------
# Create new user
# -------------------------------
def create_user(session: Session, user_create: UserCreate) -> User:
    if len(user_create.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password too short. Minimum 6 characters required."
        )

    try:
        hashed_password = get_password_hash(user_create.password)
        db_user = User(
            email=user_create.email,
            hashed_password=hashed_password
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
