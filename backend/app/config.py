from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/decision_intelligence"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LLM
    OPENAI_API_KEY: Optional[str] = None

    # App
    APP_NAME: str = "Decision Intelligence Platform"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    model_config = {"env_file": ".env"}


settings = Settings()
