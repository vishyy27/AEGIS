from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Deployment Risk Prediction API"

    DATABASE_URL: str = "sqlite:///./aegis.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "supersecretkey-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Optional integrations
    GITHUB_TOKEN: str = ""
    GITHUB_WEBHOOK_SECRET: str = "default-github-secret"

    # CI/CD webhook security token
    AEGIS_SECRET_TOKEN: str = "dev-token-123"
    
    # Production Variables
    MODEL_PATH: str = "ml/models/deployment_risk_model.pkl"
    WEBHOOK_SECRET: str = "your_dev_webhook_secret"
    LOG_LEVEL: str = "INFO"

    # Phase 9 Policy Engine Thresholds
    RISK_ALLOW_THRESHOLD: int = 40
    RISK_BLOCK_THRESHOLD: int = 70

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
