# Agent Queue

비동기 및 에이전트 기반의 문서 요약/ 체크리스트 생성 어플리케이션 입니다.

---

## 시스템 구성

- **Frontend**: React 기반 웹 인터페이스
- **Backend**: FastAPI + Celery + Redis/Postgres 기반 비동기 작업 처리
- **Agent**: ADK 기반 에이전트 서버 (GPT 체이닝 처리)

---

## 주요 기능

- 문서 업로드 및 비동기 처리
- FIFO 기반 작업 큐잉
- 실시간 작업 상태 모니터링
- 문서 요약 및 체크리스트 자동 생성

---

## 기술 스택

- FastAPI + Celery + Redis/Postgres
- React + TypeScript
- Docker + Docker Compose
- ADK (Agent Development Kit)

---

## 시작하기

```bash
# 모든 서비스 실행
docker compose up --build

# 프론트엔드 접속
http://localhost:3000

# API 문서
http://localhost:8000/docs
```

---

## AI 도구 활용

- Cursor를 활용한 코드 자동완성 및 리팩토링
- Claude를 통한 코드 리뷰 및 최적화
- Gemini를 통한 LLM 에이전트 구축

---

## 라이선스

MIT License
