"""Core configuration module using Pydantic Settings."""

from typing import List, Optional, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PLC Copilot"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Security
    SECRET_KEY: str = "not-used-yet-placeholder"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"
    TEST_DATABASE_URL: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_ASSISTANT_ID: str
    OPENAI_VECTOR_STORE_ID: str
    
    # Email Configuration for Notifications
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    NOTIFICATION_EMAIL: str = "je77petersen@gmail.com"
    
    # Sentry
    SENTRY_DSN: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["application/pdf", "text/plain"]
    UPLOAD_DIR: str = "uploads"
    
    # PLC Code Generation Settings
    DEFAULT_PLC_LANGUAGE: str = "structured_text"
    MAX_PROMPT_LENGTH: int = 4000
    DEFAULT_TEMPERATURE: float = 1.0
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()