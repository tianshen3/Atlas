from app.core.config import settings
from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    AsyncSession, 
    async_sessionmaker
)

#async connection url
if settings.DATABASE_URL:
    postgres_url = settings.DATABASE_URL
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif postgres_url.startswith("postgresql://"):
        postgres_url = postgres_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    postgres_url = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# create the async engine
engine = create_async_engine(
    postgres_url,
    echo = False,
    pool_size = 20,
    max_overflow = 10,
    pool_pre_ping = True,
)

# create async factory
AsyncSessionLocal = async_sessionmaker(
    bind = engine,
    class_ = AsyncSession,
    expire_on_commit = False,
    autoflush = False,
)

# NOTE: Use `get_db_session` from `app.api.deps` as the FastAPI dependency for DB sessions.
# The session factory `AsyncSessionLocal` is available here for use in workers/pipeline
# that operate outside the FastAPI request lifecycle.

