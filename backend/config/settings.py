"""
Application settings and configuration management.
Supports environment variables and different configuration profiles.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "spoXpro Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Database settings
    database_url: str = "sqlite:///./spoxpro.db"
    database_echo: bool = False
    
    # JWT settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # CORS settings
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # Logging settings
    log_level: str = "INFO"
    log_file_path: str = "./logs/log_file/spoxpro.log"
    log_max_file_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Cookie settings
    cookie_max_age: int = 30 * 24 * 60 * 60  # 30 days in seconds
    cookie_secure: bool = False
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"
    
    @validator("jwt_secret_key")
    def validate_jwt_secret(cls, v, values):
        """Validate JWT secret key is set in production."""
        if values.get("environment") == "production" and v == "your-secret-key-change-in-production":
            raise ValueError("JWT secret key must be set in production environment")
        return v
    
    @validator("cors_origins", pre=True)
    def validate_cors_origins(cls, v):
        """Convert string to list if needed."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings


def validate_required_settings():
    """Validate that all required settings are properly configured."""
    errors = []
    
    # Check JWT secret in production
    if settings.environment == "production":
        if settings.jwt_secret_key == "your-secret-key-change-in-production":
            errors.append("JWT_SECRET_KEY must be set in production")
    
    # Check database URL
    if not settings.database_url:
        errors.append("DATABASE_URL must be set")
    
    # Check log file path directory exists
    log_dir = os.path.dirname(settings.log_file_path)
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create log directory {log_dir}: {e}")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    return True