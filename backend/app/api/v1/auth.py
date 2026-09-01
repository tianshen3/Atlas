"""
Authentication REST Router.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import create_access_token, verify_password
from app.api.deps import get_db_session
from app.db.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """
    Authenticate user credentials against the database and issue a JWT Bearer token.
    """
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role, "tenant_id": "tenant_default"}
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
    )
