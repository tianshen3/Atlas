from app.core.config import settings
from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    AsyncSession, 
    async_sessionmaker
)

#async connection url
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

