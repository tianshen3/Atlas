from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency provider that yields an isolated async database session per request."""
    async with AsyncSessionLocal() as session:
        yield session
