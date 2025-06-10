from pydantic_settings import BaseSettings
import os
from app.core.test_config import test_settings

if os.environ.get("TESTING", "0") == "1":
    DATABASE_URL = test_settings.DATABASE_URL
else:
    DATABASE_URL = "postgresql://postgres:postgres@db:5432/guideline_db"

class Settings(BaseSettings):
    # Redis 설정
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # 데이터베이스 설정
    DATABASE_URL: str = DATABASE_URL
    
    # Celery 설정
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    
    # 기타 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Agent Queue"
    
    # Agent API 설정
    AGENT_API_URL: str = "http://agent:8001"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 