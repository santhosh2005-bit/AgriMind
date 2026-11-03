"""Core application configuration module with Pydantic Settings."""

from pathlib import Path
from typing import List
import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """AgriMind global application configuration."""

    ENVIRONMENT: str = Field(default="development", description="Environment: development, test, production")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    APP_HOST: str = Field(default="127.0.0.1", description="FastAPI host binding")
    APP_PORT: int = Field(default=8000, description="FastAPI port binding")
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated allowed CORS origins"
    )

    # Persistence & File Storage
    DATABASE_URL: str = Field(default="sqlite:///./data/agrimind.db")
    UPLOAD_DIR: str = Field(default="./data/uploads")
    KNOWLEDGE_DIR: str = Field(default="./data/knowledge")
    FAISS_INDEX_PATH: str = Field(default="./data/knowledge/faiss_index")

    # Commercial Model 1: Google Gemini (Multimodal / Vision)
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_DEFAULT_MODEL: str = Field(default="gemini-1.5-flash", description="Gemini model ID")

    # Commercial Model 2: Groq Cloud (Ultra-fast Inference / Reasoning)
    GROQ_API_KEY: str = Field(default="", description="Groq Cloud API key")
    GROQ_DEFAULT_MODEL: str = Field(default="llama-3.3-70b-versatile", description="Groq model ID")

    # Open-Weight Local Model: Ollama
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama API endpoint")
    OLLAMA_DEFAULT_MODEL: str = Field(default="llama3.2:3b", description="Ollama local model tag")

    # Tool A: Weather API
    OPEN_METEO_BASE_URL: str = Field(default="https://api.open-meteo.com/v1/forecast")
    OPENWEATHER_API_KEY: str = Field(default="")

    # Vector Embedding Configuration
    EMBEDDING_MODEL_NAME: str = Field(default="all-MiniLM-L6-v2")

    # Execution Safeguards & Budgets
    MAX_PLAN_STEPS: int = Field(default=10, ge=1, le=25)
    DEFAULT_STEP_TIMEOUT_SECONDS: int = Field(default=30, ge=5, le=120)
    WORKFLOW_EXECUTION_BUDGET_SECONDS: int = Field(default=120, ge=10, le=600)
    MAX_RETRIES_PER_STEP: int = Field(default=2, ge=0, le=5)
    ENABLE_MOCK_FALLBACKS_FOR_TESTS: bool = Field(default=True)

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def ensure_directories(self) -> None:
        """Create necessary data, upload, and knowledge directories if they do not exist."""
        for path_str in [self.UPLOAD_DIR, self.KNOWLEDGE_DIR, Path(self.DATABASE_URL.replace("sqlite:///", "")).parent]:
            p = Path(path_str)
            p.mkdir(parents=True, exist_ok=True)


settings = Settings()
