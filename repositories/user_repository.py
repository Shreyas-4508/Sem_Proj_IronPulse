"""
User repository — database query helpers for the User model.
All queries go through these functions to maintain a clean data-access layer.
"""

from typing import Optional
from sqlalchemy.orm import Session

from models.user import User


def find_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def find_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower()).first()


def find_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def find_by_email_or_username(db: Session, identifier: str) -> Optional[User]:
    return db.query(User).filter(
        (User.email == identifier.lower()) | (User.username == identifier)
    ).first()


def email_exists(db: Session, email: str) -> bool:
    return db.query(User.id).filter(User.email == email.lower()).first() is not None


def username_exists(db: Session, username: str) -> bool:
    return db.query(User.id).filter(User.username == username).first() is not None
