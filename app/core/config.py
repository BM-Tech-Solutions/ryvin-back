from pathlib import Path
from typing import Any, List, Optional

from pydantic import PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Project Description
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Ryvin Dating API"
    VERSION: str = "0.1.0"

    # SECURITY
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 14
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # JWT Authentication
    JWT_SECRET_KEY: Optional[str] = None
    REFRESH_TOKEN_EXPIRE_DAYS: Optional[int] = None

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # DATABASE
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URI: Optional[PostgresDsn] = None

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

    # Firebase Admin SDK Credentials
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = None
    FIREBASE_API_KEY: Optional[str] = None
    FIREBASE_AUTH_DOMAIN: Optional[str] = None
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_TYPE: Optional[str] = None
    FIREBASE_PROJECT_ID_ENV: Optional[str] = None
    FIREBASE_PRIVATE_KEY_ID: Optional[str] = None
    FIREBASE_PRIVATE_KEY: Optional[str] = None
    FIREBASE_CLIENT_EMAIL: Optional[str] = None
    FIREBASE_CLIENT_ID: Optional[str] = None
    FIREBASE_AUTH_URI: Optional[str] = None
    FIREBASE_TOKEN_URI: Optional[str] = None
    FIREBASE_AUTH_PROVIDER_X509_CERT_URL: Optional[str] = None
    FIREBASE_CLIENT_X509_CERT_URL: Optional[str] = None

    # Google OAuth (for Social Login)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # RATE LIMITING
    RATE_LIMIT_PER_MINUTE: int = 100

    # API SECURITY
    API_TOKEN: str

    # Twilio
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_API_KEY_SID: str = ""
    TWILIO_API_KEY_SECRET: str = ""
    TWILIO_SERVICE_SID: str = ""
    TWILIO_SERVICE_ROLE_SID: str = ""
    TWILIO_CHANNEL_ROLE_SID: str = ""
    TWILIO_ACCESS_TOKEN_TTL_SECONDS: int = 60 * 60 * 24 * 7
    TWILIO_CHAT_WEBHOOK_URL: str = ""
    TWILIO_VIDEO_WEBHOOK_URL: str = ""
    TWILIO_WEBHOOK_URL: str = ""

    # Base Directory
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v

        # Get values from the model being validated
        data = info.data

        # Get all the database connection components
        user = data.get("POSTGRES_USER")
        password = data.get("POSTGRES_PASSWORD")
        host = data.get("POSTGRES_SERVER")
        port = data.get("POSTGRES_PORT")
        db = data.get("POSTGRES_DB", "")

        # Manually construct the connection string to ensure correct format
        # Format: postgresql+psycopg2://user:password@host:port/dbname
        connection_str = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

        # Return as PostgresDsn
        return connection_str


settings = Settings()
