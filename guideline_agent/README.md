# Agent Queue Agent Server

ADK(Agent Development Kit)를 사용하여 구현된 문서 처리 에이전트 서버입니다.

## 주요 기능

- 문서 요약 및 체크리스트 생성
- 에이전트 기반 대화형 처리
- 세션 기반 상태 관리
- 비동기 이벤트 처리

## 기술 스택

- ADK (Agent Development Kit)
- FastAPI
- aiohttp

## 아키텍처

- **에이전트 기반 처리**: ADK를 통한 에이전트 기반 문서 처리
- **세션 관리**: 사용자별 세션 기반 상태 관리
- **이벤트 기반**: 비동기 이벤트를 통한 처리 결과 전달
- **확장성**: 다양한 에이전트 타입 지원 (summary_agent, checklist_agent)

## 개발 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
adk api_server --host 0.0.0.0 --port 8001
```

## API 엔드포인트

- **세션 생성**: POST /apps/guideline_agent/users/{user_id}/sessions/{session_id}
- **문서 처리**: POST /run

## AI 도구 활용

- ADK를 통한 에이전트 로직 자동 생성
- Cursor를 활용한 API 엔드포인트 구현
