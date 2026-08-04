from pydantic_settings import SettingsConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "ATLAS Enterprise Hybrid RAG"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"

    #Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    #Database Defaults
    POSTGRES_USER: str = "atlas_user"
    POSTGRES_PASSWORD: str = "atlas_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "atlas_db"

    #VectorDB(Qdrant) & Cache(Redis)
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379


#Instantiating settings globally
settings = Settings()