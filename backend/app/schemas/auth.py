"""
Authentication Pydantic schemas (DTOs).
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Credentials payload for the /auth/token endpoint."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """JWT Bearer token response returned after successful login."""
    access_token: str
    token_type: str = "bearer"
    role: str

