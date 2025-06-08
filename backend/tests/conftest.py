import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
import os

@pytest.fixture(scope="session")
def db_engine():
    """테스트용 데이터베이스 엔진 생성"""
    # 테스트 데이터베이스 URL 설정
    TEST_DATABASE_URL = "postgresql://postgres:postgres@test_db:5432/test_agent_que"
    
    # 기본 데이터베이스에 연결
    engine = create_engine("postgresql://postgres:postgres@test_db:5432/postgres")
    
    # 데이터베이스가 없으면 생성
    with engine.connect() as conn:
        conn.execute(text("COMMIT"))
        conn.execute(text("DROP DATABASE IF EXISTS test_agent_que WITH (FORCE)"))
        conn.execute(text("CREATE DATABASE test_agent_que"))
    
    # 테스트 데이터베이스에 연결
    test_engine = create_engine(TEST_DATABASE_URL)
    
    # 테이블 생성
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine
    
    # 테스트 후 정리
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    
    with engine.connect() as conn:
        conn.execute(text("COMMIT"))
        conn.execute(text("DROP DATABASE IF EXISTS test_agent_que WITH (FORCE)"))
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """테스트용 데이터베이스 세션 생성"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    
    yield session
    
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