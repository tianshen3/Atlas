from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.services.retrieval_service import RetrievalService
from app.services.chat_service import ChatService

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency provider that yields an isolated async database session per request."""
    async with AsyncSessionLocal() as session:
        yield session


def get_retrieval_service() -> RetrievalService:
    """FastAPI dependency provider for RetrievalService."""
    return RetrievalService()

def get_chat_service() -> ChatService:
    """ FastAPI dependency provider for Chat Service"""
    return ChatService()

