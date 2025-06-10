import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.test_config import test_settings
import os
import shutil
from app.models.job import Job
import redis
from unittest.mock import MagicMock, patch
from app.core.celery_app import celery_app

@pytest.fixture(scope="function")
def mock_redis():
    """Redis 연결을 모킹합니다."""
    mock = MagicMock()
    mock.ping.return_value = True
    mock.hset.return_value = True
    mock.hgetall.return_value = {}
    return mock

@pytest.fixture(scope="function", autouse=True)
def setup_redis_mock(mock_redis):
    """Redis 클라이언트를 모킹으로 대체합니다."""
    with patch('app.tasks.process_guideline.redis_client', mock_redis):
        yield

@pytest.fixture(scope="function", autouse=True)
def setup_celery():
    """Celery 설정을 테스트 환경에 맞게 수정합니다."""
    celery_app.conf.update(
        broker_url='memory://',
        result_backend='cache+memory://',
        task_always_eager=True,
        task_eager_propagates=True
    )
    yield
    celery_app.conf.update(
        broker_url=test_settings.CELERY_BROKER_URL,
        result_backend=test_settings.CELERY_RESULT_BACKEND,
        task_always_eager=False,
        task_eager_propagates=False
    )

@pytest.fixture(scope="session")
def db_engine():
    """테스트용 데이터베이스 엔진 생성"""
    # 기본 데이터베이스에 연결
    default_engine = create_engine("postgresql://postgres:postgres@localhost:5432/postgres")
    
    # 테스트 데이터베이스가 없으면 생성
    with default_engine.connect() as conn:
        conn.execute(text("COMMIT"))
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_settings.DATABASE_URL.split('/')[-1]} WITH (FORCE)"))
        conn.execute(text(f"CREATE DATABASE {test_settings.DATABASE_URL.split('/')[-1]}"))
    
    # 테스트 데이터베이스에 연결
    engine = create_engine(test_settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # 테스트 후 정리
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    
    with default_engine.connect() as conn:
        conn.execute(text("COMMIT"))
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_settings.DATABASE_URL.split('/')[-1]} WITH (FORCE)"))
    default_engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """테스트용 데이터베이스 세션 생성"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_pdf_file():
    """테스트용 PDF 파일 생성"""
    test_file_path = "test_guideline.pdf"
    with open(test_file_path, "wb") as f:
        f.write(b"%PDF-1.4\n%Test PDF file")
    
    yield test_file_path
    
    if os.path.exists(test_file_path):
        os.remove(test_file_path)

@pytest.fixture(scope="function")
def test_upload_dir():
    """테스트용 업로드 디렉토리를 생성합니다."""
    test_dir = test_settings.UPLOAD_DIR
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    yield test_dir
    shutil.rmtree(test_dir)

@pytest.fixture(scope="function")
def sample_job(db_session):
    """샘플 작업을 생성합니다."""
    job = Job(
        id="test-job-id",
        status="pending",
        result={}
    )
    db_session.add(job)
    db_session.commit()
    return job 