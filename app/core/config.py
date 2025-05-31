import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Ryvin Dating API"
    VERSION: str = "0.1.0"
    
    # SECURITY
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # DATABASE
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ryvin"
    POSTGRES_PORT: str = "5432"
    DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str):
            return v
        
        # Get values from the model being validated
        data = info.data
        
        # Get all the database connection components
        user = data.get("POSTGRES_USER")
        password = data.get("POSTGRES_PASSWORD")
        host = data.get("POSTGRES_SERVER")
        port = data.get("POSTGRES_PORT")
        db = data.get("POSTGRES_DB") or ""
        
        # Manually construct the connection string to ensure correct format
        # Format: postgresql+psycopg2://user:password@host:port/dbname
        connection_str = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
        
        # Return as PostgresDsn
        return connection_str
    
    # SMS SERVICE
    SMS_PROVIDER_API_KEY: str = ""
    SMS_VERIFICATION_TEMPLATE: str = "Your Ryvin verification code is: {code}"
    
    # STORAGE
    STORAGE_BACKEND: str = "local"  # Options: local, s3
    STORAGE_DIR: str = "media"  # For local storage
    
    # S3 STORAGE (if used)
    S3_BUCKET_NAME: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_REGION: Optional[str] = None
    
    # RATE LIMITING
    RATE_LIMIT_PER_MINUTE: int = 100


settings = Settings()
