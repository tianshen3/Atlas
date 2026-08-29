"""
Authentication REST Router.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.core.security import create_access_token, verify_password, get_password_hash

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str
    tenant_id: str = "default"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str


DEMO_USERS = {
    "admin": {
        "username": "admin",
        "password": "secret123",
        "tenant_id": "tenant_default",
    }
}


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(request: LoginRequest) -> TokenResponse:
    """
    Authenticate user credentials and issue OAuth2 Bearer JWT token.
    """
    user = DEMO_USERS.get(request.username)
    if not user or user["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tenant_id = request.tenant_id or user["tenant_id"]
    access_token = create_access_token(
        data={"sub": user["username"], "tenant_id": tenant_id}
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        tenant_id=tenant_id,
    )
