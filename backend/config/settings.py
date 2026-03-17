"""
Application settings and configuration management.
Supports environment variables and different configuration profiles.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator
from typing import List

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
    jwt_secret_key: str = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w9x0y1z2"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 120
    
    # CORS settings
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    cors_allow_credentials: bool = False
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # Logging settings
    log_level: str = "WARNING"
    log_file_path: str = "./logs/log_file/spoxpro.log"
    log_max_file_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Cookie settings
    cookie_max_age: int = 30 * 24 * 60 * 60  # 30 days in seconds
    cookie_secure: bool = False
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"
    
    # Upload settings
    images_path: str = r"C:\Users\lol\work\spoXpro\frontend\public\img\upload_dir\images"
    images_url_prefix: str = "/upload_dir/images"
    
    # Admin settings
    admin_username: str = "admin"
    admin_password: str = "admin"
    
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