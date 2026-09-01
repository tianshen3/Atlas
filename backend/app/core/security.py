"""
Security utilities for password hashing and JWT access token handling.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt

from app.core.config import settings


def get_password_hash(password: str) -> str:
    """Generate a secure bcrypt password hash with an automatic per-user salt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain text password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Encode JWT access token with expiration timestamp.

    Args:
        data: Dictionary of claims to include in the token payload.
        expires_delta: Optional expiration timedelta (defaults to 15 minutes).

    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=15)

    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT access token.

    Args:
        token: JWT string.

    Returns:
        Decoded payload dictionary.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
    )
    return payload
