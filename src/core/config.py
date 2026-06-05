from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Core ---
    DATABASE_URL: str = "postgres://halwall_user:halwall_password@localhost:5433/halwall"
    DATABASE_READ_URL: Optional[str] = None  # Read replica URL (falls back to DATABASE_URL)
    REDIS_URL: str = "redis://localhost:6380/0"
    SECRET_KEY: str = "change-me-in-production"

    # --- Database Gate ---
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30  # seconds to wait for a connection from the pool
    DB_POOL_RECYCLE: int = 1800  # seconds before a connection is recycled
    DB_STATEMENT_TIMEOUT_MS: int = 30000  # 30s max query execution
    DB_LOCK_TIMEOUT_MS: int = 10000  # 10s max lock wait
    DB_CIRCUIT_BREAKER_THRESHOLD: int = 5  # failures before circuit opens
    DB_CIRCUIT_BREAKER_TIMEOUT: float = 30.0  # seconds before retry after circuit opens
    DB_ECHO: bool = False  # SQL logging (disable in production)
    DB_SSL_REQUIRED: bool = True  # Require SSL for DB connections (Render, most cloud providers)

    # --- Rate Limiting ---
    DEFAULT_RATE_LIMIT: int = 30  # requests per minute for unauthenticated clients

    # --- Application ---
    ENVIRONMENT: str = "development"  # development, staging, production
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = ""  # Comma-separated list of allowed origins

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
