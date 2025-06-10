from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from app.api import jobs
from app.core.database import Base, SessionLocal, get_db
import logging
import time
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 테스트 환경과 일반 환경의 DB 연결 분리
if os.environ.get("TESTING", "0") == "1":
    from app.core.test_config import test_settings
    DATABASE_URL = test_settings.DATABASE_URL
else:
    from app.core.config import settings
    DATABASE_URL = settings.DATABASE_URL

# 데이터베이스 엔진 생성
engine = create_engine(DATABASE_URL)

# 테스트 환경이 아닐 때만 테이블 생성
if os.environ.get("TESTING", "0") != "1":
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document Processing API",
    description="""
    문서 처리 API 서버입니다.
    
    ## 기능
    * PDF 문서 업로드 및 처리
    * 문서 요약 및 체크리스트 생성
    * 작업 상태 조회
    
    ## 사용 방법
    1. 문서 업로드: POST /jobs/
    2. 작업 상태 조회: GET /jobs/{job_id}
    """,
    version="1.0.0",
    docs_url=None,  # 기본 Swagger UI 비활성화
    redoc_url=None  # 기본 ReDoc UI 비활성화
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 프론트엔드 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 응답 시간 측정 미들웨어
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Request to {request.url.path} took {process_time:.3f} seconds")
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 커스텀 OpenAPI 스키마 생성
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # API 서버 정보 추가
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 커스텀 Swagger UI 엔드포인트
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )

# 라우터 등록 (prefix 제거)
app.include_router(jobs.router, tags=["jobs"]) 