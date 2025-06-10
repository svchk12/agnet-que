from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
import aiohttp
import asyncio
import json
from typing import Dict, Any
import uuid
import logging
import os
import PyPDF2
import docx
import chardet
from datetime import datetime
from redis import Redis
from app.core.config import settings
import re
import redis
import requests
import io

logger = logging.getLogger(__name__)

# 에이전트 서버 URL을 설정에서 가져오기
AGENT_SERVER_URL = settings.AGENT_API_URL

# Redis 클라이언트 설정
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True
)

# Redis 연결 테스트
try:
    redis_client.ping()
except redis.ConnectionError as e:
    logger.error(f"Failed to connect to Redis: {e}")
    # 테스트 환경에서는 Redis 연결 실패를 무시
    if os.environ.get("TESTING", "0") != "1":
        raise

def update_job_status(job_id: str, status: JobStatus, data: dict):
    """Redis에 작업 상태를 업데이트합니다."""
    redis_data = {
        "status": status,
        **data,
        "updated_at": datetime.now().isoformat()
    }
    redis_client.hset(f"job:{job_id}", mapping=redis_data)
    logger.debug(f"Updated Redis data for job {job_id}: {redis_data}")

def handle_job_failure(job_id: str, error: Exception):
    """작업 실패 시 DB와 Redis를 업데이트합니다."""
    # DB 업데이트
    with SessionLocal() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.result = json.dumps({"error": str(error)})
            db.commit()
    
    # Redis 업데이트
    update_job_status(job_id, JobStatus.FAILED, {
        "error": str(error),
        "failed_at": datetime.now().isoformat()
    })

def extract_text_from_file(file_path: str) -> str:
    """파일 형식에 따라 텍스트를 추출합니다."""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.pdf':
            return extract_text_from_pdf(file_path)
        elif file_ext in ['.doc', '.docx']:
            return extract_text_from_doc(file_path)
        elif file_ext == '.txt':
            return extract_text_from_txt(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {file_ext}")
    except Exception as e:
        logger.error(f"파일 텍스트 추출 실패: {str(e)}")
        raise

def extract_text_from_pdf(file_path: str) -> str:
    """PDF 파일에서 텍스트를 추출합니다."""
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def extract_text_from_doc(file_path: str) -> str:
    """DOC/DOCX 파일에서 텍스트를 추출합니다."""
    doc = docx.Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text.strip()

def extract_text_from_txt(file_path: str) -> str:
    """TXT 파일에서 텍스트를 추출합니다."""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding']
    
    with open(file_path, 'r', encoding=encoding) as file:
        return file.read().strip()

async def create_agent_session() -> str:
    """에이전트 서버에 세션을 생성합니다."""
    session_id = str(uuid.uuid4())
    user_id = "u_123"  # 임시 사용자 ID
    
    logger.info(f"Creating agent session with ID: {session_id}")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{AGENT_SERVER_URL}/apps/guideline_agent/users/{user_id}/sessions/{session_id}"
            async with session.post(url, json={"state": {}}) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"에이전트 세션 생성 실패: {error_text}")
                return session_id
    except Exception as e:
        logger.error(f"Error creating agent session: {str(e)}")
        raise

async def process_with_agent(session_id: str, content: str) -> Dict[str, Any]:
    """에이전트를 통해 문서를 처리합니다."""
    user_id = "u_123"  # 임시 사용자 ID
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{AGENT_SERVER_URL}/run"
            async with session.post(
                url,
                json={
                    "appName": "guideline_agent",
                    "userId": user_id,
                    "sessionId": session_id,
                    "newMessage": {
                        "role": "user",
                        "parts": [{"text": content}]
                    }
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"에이전트 처리 실패: {error_text}")
                
                events = await response.json()
                if not events:
                    raise Exception("에이전트 응답이 없습니다.")
                
                summary = ""
                checklist = []
                
                for event in events:
                    if not event.get("actions") or not event["actions"].get("stateDelta"):
                        continue
                    
                    state_delta = event["actions"]["stateDelta"]
                    author = event.get("author", "")
                    
                    if author == "summary_agent" and "summary" in state_delta:
                        summary = state_delta["summary"]
                    elif author == "checklist_agent" and "checklist" in state_delta:
                        checklist_text = state_delta["checklist"]
                        checklist_items = [
                            re.sub(r'^\d+\.\s*', '', line.strip())
                            for line in checklist_text.split('\n')
                            if line.strip() and not line.strip().startswith('[') and not line.strip().endswith(']')
                        ]
                        checklist = [item for item in checklist_items if item]
                
                if not summary and not checklist:
                    raise Exception("요약과 체크리스트가 모두 비어있습니다.")
                
                return {
                    "summary": summary,
                    "checklist": checklist
                }
    except Exception as e:
        logger.error(f"Error in process_with_agent: {str(e)}")
        raise

@celery_app.task(name="app.tasks.process_guideline.process_guideline")
def process_guideline(job_id: str, filename: str):
    """가이드라인 문서를 처리하는 Celery 작업"""
    logger.info(f"Starting job processing for job_id: {job_id}, filename: {filename}")
    db = SessionLocal()
    
    try:
        # 작업 시작 시 상태 업데이트
        start_time = datetime.now().isoformat()
        update_job_status(job_id, JobStatus.PROCESSING, {
            "filename": filename,
            "started_at": start_time,
            "summary": "",
            "checklist": "[]"
        })

        # 작업 상태를 'processing'으로 업데이트
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise Exception("Job not found")
        
        job.status = JobStatus.PROCESSING
        db.commit()

        # 파일 내용 읽기
        file_path = f"uploads/{filename}"
        if not os.path.exists(file_path):
            raise Exception("File not found")

        file_content = extract_text_from_file(file_path)
        if not file_content.strip():
            raise Exception("File is empty")

        # 비동기 작업 실행
        loop = asyncio.get_event_loop()
        session_id = loop.run_until_complete(create_agent_session())
        result = loop.run_until_complete(process_with_agent(session_id, file_content))

        # 작업 완료 처리
        job.status = JobStatus.COMPLETED
        job.result = result
        db.commit()

        # 최종 결과 저장
        update_job_status(job_id, JobStatus.COMPLETED, {
            "summary": result["summary"],
            "checklist": json.dumps(result["checklist"], ensure_ascii=False),
            "completed_at": datetime.now().isoformat(),
            "started_at": start_time,
            "filename": filename
        })

        return {
            "status": JobStatus.COMPLETED,
            "summary": result["summary"],
            "checklist": result["checklist"]
        }

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        handle_job_failure(job_id, e)
        raise
    finally:
        db.close()
        logger.info(f"Job processing finished: {job_id}") 