from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgres://halwall_user:halwall_password@localhost:5433/halwall"
    REDIS_URL: str = "redis://localhost:6380/0"
    SECRET_KEY: str = "supersecretkey"
    
    class Config:
        env_file = ".env"

settings = Settings()
