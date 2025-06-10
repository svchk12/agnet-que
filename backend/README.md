# Agent Queue Backend

FastAPI와 Celery를 사용한 비동기 문서 처리 백엔드 서버입니다.

## 주요 기능

- 문서 업로드 및 작업 큐잉 (POST /jobs)
- 작업 상태 및 결과 조회 (GET /jobs/{job_id})
- Redis를 통한 실시간 작업 상태 업데이트
- PostgreSQL을 통한 작업 결과 영구 저장

## 기술 스택

- FastAPI
- Celery + Redis
- PostgreSQL
- SQLAlchemy
- Pydantic

## 아키텍처

- **비동기 작업 처리**: Celery worker가 FIFO 방식으로 작업을 처리
- **상태 관리**: Redis를 통한 실시간 상태 업데이트
- **데이터 저장**: PostgreSQL을 통한 영구 저장
- **에이전트 연동**: HTTP를 통한 agent 서버와의 통신

## 개발 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn app.main:app --reload

# Celery worker 실행
celery -A app.core.celery_app worker --loglevel=info
```

## API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## AI 도구 활용

- Cursor를 통한 API 엔드포인트 자동 생성
- Cursor를 통한 테스트 코드 작성 및 테스트 진행

## 테스트

TESTING=1 PYTHONPATH=$PYTHONPATH:. pytest tests/ -v
