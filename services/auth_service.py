"""
Authentication service — registration, login, password management.
All password hashing and verification happens here.
Never store plain-text passwords.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from config import settings
from models.user import User
from models.profile import UserProfile

logger = logging.getLogger(__name__)

# --- Validation constants ---
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,50}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(Exception):
    """Raised for authentication and registration failures."""
    pass


def _hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt."""
    if not plain:
        raise AuthError("Password cannot be empty.")
    encoded = plain.encode("utf-8")
    hashed = bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS))
    return hashed.decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _validate_registration_input(
    email: str, username: str, password: str, confirm_password: str
) -> None:
    """
    Raises AuthError if registration fields fail validation.
    Does NOT touch the database.
    """
    email = email.strip()
    username = username.strip()

    if not email or not EMAIL_PATTERN.match(email):
        raise AuthError("Please enter a valid email address.")

    if not username or not USERNAME_PATTERN.match(username):
        raise AuthError(
            "Username must be 3–50 characters and contain only letters, numbers, or underscores."
        )

    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

    if len(password) > MAX_PASSWORD_LENGTH:
        raise AuthError("Password is too long.")

    if password != confirm_password:
        raise AuthError("Passwords do not match.")


def register_user(
    db: Session,
    email: str,
    username: str,
    password: str,
    confirm_password: str,
) -> User:
    """
    Creates a new user account.
    Returns the created User on success.
    Raises AuthError on validation failure or duplicate accounts.
    """
    email = email.strip().lower()
    username = username.strip()

    _validate_registration_input(email, username, password, confirm_password)

    # Check duplicates before attempting insert
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise AuthError("An account with this email address already exists.")

    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        raise AuthError("This username is already taken. Please choose another.")

    try:
        password_hash = _hash_password(password)
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        db.flush()  # Get user.id before committing

        # Create an empty profile for the new user
        profile = UserProfile(
            user_id=user.id,
            display_name=username,
            onboarding_complete=False,
        )
        db.add(profile)
        db.flush()

        logger.info("Registered new user: %s (id=%s)", username, user.id)
        return user

    except IntegrityError as exc:
        db.rollback()
        logger.warning("IntegrityError during registration: %s", exc)
        raise AuthError(
            "Registration failed due to a conflict. The email or username may already be in use."
        )
    except Exception as exc:
        db.rollback()
        logger.error("Unexpected error during registration: %s", exc)
        raise


def login_user(db: Session, email_or_username: str, password: str) -> User:
    """
    Authenticates a user by email or username plus password.
    Returns the User on success.
    Raises AuthError on invalid credentials or inactive accounts.
    """
    identifier = email_or_username.strip()

    if not identifier or not password:
        raise AuthError("Please enter your email/username and password.")

    # Lookup by email or username
    user = db.query(User).filter(
        (User.email == identifier.lower()) | (User.username == identifier)
    ).first()

    if user is None:
        raise AuthError("Invalid email/username or password.")

    if not user.is_active:
        raise AuthError("This account has been deactivated. Please contact support.")

    if not _verify_password(password, user.password_hash):
        raise AuthError("Invalid email/username or password.")

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.flush()

    logger.info("User logged in: %s (id=%s)", user.username, user.id)
    return user


def change_password(
    db: Session, user_id: int, current_password: str, new_password: str, confirm_new: str
) -> None:
    """
    Changes a user's password after verifying the current one.
    Raises AuthError on failure.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise AuthError("User not found.")

    if not _verify_password(current_password, user.password_hash):
        raise AuthError("Current password is incorrect.")

    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"New password must be at least {MIN_PASSWORD_LENGTH} characters.")

    if len(new_password) > MAX_PASSWORD_LENGTH:
        raise AuthError("New password is too long.")

    if new_password != confirm_new:
        raise AuthError("New passwords do not match.")

    if current_password == new_password:
        raise AuthError("New password must differ from the current password.")

    user.password_hash = _hash_password(new_password)
    db.flush()
    logger.info("Password changed for user id=%s", user_id)


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Returns a User by primary key, or None if not found."""
    return db.query(User).filter(User.id == user_id).first()


def deactivate_user(db: Session, user_id: int) -> None:
    """Soft-deletes a user account by marking it inactive."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = False
        db.flush()
        logger.info("Deactivated user id=%s", user_id)
