from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.services.retrieval_service import RetrievalService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency provider that yields an isolated async database session per request."""
    async with AsyncSessionLocal() as session:
        yield session


def get_retrieval_service() -> RetrievalService:
    """FastAPI dependency provider for RetrievalService."""
    return RetrievalService()

