import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "GameHub API"
    API_V1_STR: str = "/api"
    DEBUG: bool = True

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "gamehub_db"
    DATABASE_URL: Optional[str] = None
    USE_SQLITE_FALLBACK: bool = False

    # Gemini / LLM
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-flash-lite-latest"
    GEMINI_MODELS: str = "gemini-flash-lite-latest,gemini-flash-latest,gemini-3.5-flash-lite,gemini-3.6-flash"
    GEMINI_TEMPERATURE: float = 0.0

    # OpenAI / Alternative LLM option
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_PROVIDER: str = "gemini"  # "gemini", "openai", or "mock"

    # ChromaDB Semantic Search
    CHROMA_ENABLED: bool = True

    # Assistant Backend API Client
    BACKEND_API_BASE_URL: str = "http://127.0.0.1:8000/api"
    API_CLIENT_TIMEOUT: float = 15.0
    API_CLIENT_MAX_RETRIES: int = 3
    API_CLIENT_USE_ASGI: bool = True

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.USE_SQLITE_FALLBACK:
            return "sqlite:///./gamehub.db"
        # URL encode password in case it has special characters
        import urllib.parse
        encoded_password = urllib.parse.quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    @property
    def root_mysql_url(self) -> str:
        import urllib.parse
        encoded_password = urllib.parse.quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/?charset=utf8mb4"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
