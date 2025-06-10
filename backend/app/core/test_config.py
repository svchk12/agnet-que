from pydantic_settings import BaseSettings
from typing import Optional

class TestSettings(BaseSettings):
    """테스트 환경 설정"""
    # 데이터베이스 설정
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5434/guideline_test_db"
    
    # Redis 설정
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6380
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6380/0"
    
    # Celery 설정
    CELERY_BROKER_URL: str = "redis://localhost:6380/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6380/0"
    
    # 에이전트 서버 설정
    AGENT_API_URL: str = "http://localhost:8001"
    
    # 업로드 디렉토리 설정
    UPLOAD_DIR: str = "uploads"
    
    class Config:
        env_file = ".env.test"

test_settings = TestSettings() 