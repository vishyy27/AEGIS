import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Deployment Risk Prediction API"

    # Use SQLite for development
    DATABASE_URL: str = "sqlite:///./aegis.db"

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecretkey-change-in-production")

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Optional integrations
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
