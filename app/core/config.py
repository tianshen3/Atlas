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
    API_V1_STR: str = "/api/v1"

    #Server Settings
    HOST: str = "[0.0.0.0]"
    PORT: int = 8000

    #Database Defaults
    POSTGRES_USER: str = "atlas_user"
    POSTGRES_PASSWORD: str = "atlas_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "atlas_db"

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "atlas_super_secret_key_v1"

    #LLM Provider Configuration (OpenAI-Compatible Free/Hosted Cloud APIs)
    LLM_PROVIDER: str = "openrouter"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_TIMEOUT_SECONDS: float = 30.0
    LLM_MAX_TOKENS: int = 1000
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_RETRIES: int = 3



#Instantiating settings globally by creating an object of the Settings class
settings = Settings()