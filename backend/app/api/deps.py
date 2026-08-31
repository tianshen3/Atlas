"""
FastAPI dependency providers.
Embedding engines and services are held as module-level singletons to avoid
reloading ~100MB ML models on every request.
"""

from typing import AsyncGenerator
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.rag.embeddings import DenseEmbeddingEngine, SparseEmbeddingEngine
from app.rag.qdrant import QdrantVectorService
from app.services.chat_service import ChatService
from app.services.retrieval_service import RetrievalService

# ---------------------------------------------------------------------------
# Module-level singletons — instantiated once on first request, then reused
# ---------------------------------------------------------------------------
_dense_engine: DenseEmbeddingEngine | None = None
_sparse_engine: SparseEmbeddingEngine | None = None
_qdrant_service: QdrantVectorService | None = None
_retrieval_service: RetrievalService | None = None
_chat_service: ChatService | None = None

_http_bearer = HTTPBearer()


# ---------------------------------------------------------------------------
# DB Session (per-request, not a singleton)
# ---------------------------------------------------------------------------

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an isolated async DB session per request."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_http_bearer),
) -> dict:
    """
    Decode JWT Bearer token and return the authenticated user identity.

    Returns:
        dict with keys: id (str UUID), email (str), role (str)

    Raises:
        HTTP 401 if token is missing, expired, or invalid.
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )
        user_id: str | None = payload.get("sub")
        email: str | None = payload.get("email")
        role: str | None = payload.get("role", "user")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
            )

        return {"id": user_id, "email": email, "role": role}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )


# ---------------------------------------------------------------------------
# Singleton accessors
# ---------------------------------------------------------------------------

def get_dense_engine() -> DenseEmbeddingEngine:
    global _dense_engine
    if _dense_engine is None:
        _dense_engine = DenseEmbeddingEngine()
    return _dense_engine


def get_sparse_engine() -> SparseEmbeddingEngine:
    global _sparse_engine
    if _sparse_engine is None:
        _sparse_engine = SparseEmbeddingEngine()
    return _sparse_engine


def get_qdrant_service() -> QdrantVectorService:
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantVectorService()
    return _qdrant_service


def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService(
            embedding_engine=get_dense_engine(),
            sparse_embedding_engine=get_sparse_engine(),
            qdrant_service=get_qdrant_service(),
        )
    return _retrieval_service


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService(
            retrieval_service=get_retrieval_service(),
        )
    return _chat_service
