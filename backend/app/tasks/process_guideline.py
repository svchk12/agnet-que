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

logger = logging.getLogger(__name__)

# 에이전트 서버 URL을 설정에서 가져오기
AGENT_SERVER_URL = settings.AGENT_API_URL

# Redis 연결 설정 수정
redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

# Redis 연결 테스트
try:
    redis_client.ping()
    logger.info("Successfully connected to Redis")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    raise

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
        raise Exception(f"파일 텍스트 추출 실패: {str(e)}")

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
    # 파일 인코딩 감지
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding']
    
    # 감지된 인코딩으로 파일 읽기
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
            logger.info(f"Requesting URL: {url}")
            async with session.post(
                url,
                json={"state": {}}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Session creation failed: {error_text}")
                    raise Exception(f"에이전트 세션 생성 실패: {error_text}")
                data = await response.json()
                logger.info(f"Session created successfully: {data}")
                return session_id
    except Exception as e:
        logger.error(f"Error creating agent session: {str(e)}")
        raise

async def process_with_agent(session_id: str, content: str) -> Dict[str, Any]:
    """에이전트를 통해 문서를 처리합니다."""
    user_id = "u_123"  # 임시 사용자 ID
    
    logger.info(f"Processing content with agent, session_id: {session_id}")
    logger.info(f"Content length: {len(content)} characters")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{AGENT_SERVER_URL}/run"
            logger.info(f"Sending content to agent: {url}")
            
            async with session.post(
                url,
                json={
                    "appName": "guideline_agent",
                    "userId": user_id,
                    "sessionId": session_id,
                    "newMessage": {
                        "role": "user",
                        "parts": [{
                            "text": content
                        }]
                    }
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Agent request failed: {error_text}")
                    raise Exception(f"에이전트 처리 실패: {error_text}")
                
                events = await response.json()
                logger.info(f"Number of events received: {len(events)}")
                
                if not events:
                    raise Exception("에이전트 응답이 없습니다.")
                
                summary = ""
                checklist = []
                
                # 모든 이벤트 처리
                for event in events:
                    logger.info(f"Processing event from {event.get('author', 'unknown')}")
                    
                    if not event.get("actions") or not event["actions"].get("stateDelta"):
                        logger.warning("Event missing actions or stateDelta")
                        continue
                    
                    state_delta = event["actions"]["stateDelta"]
                    author = event.get("author", "")
                    
                    if author == "summary_agent" and "summary" in state_delta:
                        summary = state_delta["summary"]
                        logger.info(f"Found summary in stateDelta: {summary[:100]}...")
                    elif author == "checklist_agent" and "checklist" in state_delta:
                        checklist_text = state_delta["checklist"]
                        logger.info(f"Found checklist in stateDelta: {checklist_text}")
                        
                        # 체크리스트 항목 처리
                        checklist_items = []
                        lines = checklist_text.split('\n')
                        
                        for line in lines:
                            line = line.strip()
                            # 번호와 점 제거
                            line = re.sub(r'^\d+\.\s*', '', line)
                            
                            # 제목이나 빈 줄이 아닌 경우에만 처리
                            if line and not line.startswith('[') and not line.endswith(']'):
                                checklist_items.append(line)
                        
                        # 빈 항목 제거
                        checklist = [item for item in checklist_items if item]
                        logger.info(f"Processed checklist items: {checklist}")
                
                if not summary and not checklist:
                    logger.error("No summary or checklist found in events")
                    raise Exception("요약과 체크리스트가 모두 비어있습니다.")
                
                logger.info(f"Final summary: {summary[:100]}...")
                logger.info(f"Final checklist: {checklist}")
                
                return {
                    "summary": summary,
                    "checklist": checklist
                }
    except Exception as e:
        logger.error(f"Error in process_with_agent: {str(e)}")
        raise

@celery_app.task(name="app.tasks.process_guideline.process_guideline")
def process_guideline(job_id: str, filename: str):
    """
    가이드라인 문서를 처리하는 Celery 작업
    """
    logger.info(f"Starting job processing for job_id: {job_id}, filename: {filename}")
    db = SessionLocal()
    job = None
    try:
        # 작업 시작 시 상태 업데이트
        start_time = datetime.now().isoformat()
        initial_redis_data = {
            "status": JobStatus.PROCESSING,
            "filename": filename,
            "started_at": start_time,
            "summary": "",
            "checklist": "[]"
        }
        logger.info(f"Setting initial Redis data: {initial_redis_data}")
        redis_client.delete(f"job:{job_id}")  # 기존 데이터 삭제
        redis_client.hset(f"job:{job_id}", mapping=initial_redis_data)

        # Redis에 저장된 초기 데이터 확인
        initial_saved_data = redis_client.hgetall(f"job:{job_id}")
        logger.info(f"Initial saved Redis data: {initial_saved_data}")

        # 작업 상태를 'processing'으로 업데이트
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job not found: {job_id}")
            raise Exception("Job not found")

        job.status = JobStatus.PROCESSING
        db.commit()
        logger.info(f"Job status updated to processing: {job_id}")

        # 파일 내용 읽기
        file_path = f"uploads/{filename}"  # 업로드된 파일 경로
        if not os.path.exists(file_path):
            raise Exception("File not found")

        try:
            file_content = extract_text_from_file(file_path)
            if not file_content.strip():
                raise Exception("File is empty")
            logger.info(f"File content extracted successfully: {len(file_content)} characters")
        except Exception as e:
            logger.error(f"Error extracting file content: {str(e)}")
            raise Exception(f"파일 내용 추출 실패: {str(e)}")

        # 비동기 작업 실행
        loop = asyncio.get_event_loop()
        logger.info("Creating agent session")
        session_id = loop.run_until_complete(create_agent_session())
        logger.info(f"Agent session created: {session_id}")

        logger.info("Processing with agent")
        result = loop.run_until_complete(process_with_agent(session_id, file_content))
        logger.info(f"Agent processing completed: {result}")

        # 작업 상태와 결과 업데이트
        job.status = JobStatus.COMPLETED
        job.result = result
        db.commit()
        logger.info(f"Job completed successfully: {job_id}")

        # 작업 완료 시 결과 저장
        completed_time = datetime.now().isoformat()
        final_redis_data = {
            "status": JobStatus.COMPLETED,
            "summary": result["summary"],
            "checklist": json.dumps(result["checklist"], ensure_ascii=False),
            "completed_at": completed_time,
            "started_at": start_time,
            "filename": filename
        }
        logger.info(f"Setting final Redis data: {final_redis_data}")

        # Redis 데이터 업데이트
        redis_client.delete(f"job:{job_id}")  # 기존 데이터 삭제
        redis_client.hset(f"job:{job_id}", mapping=final_redis_data)

        # Redis에 저장된 최종 데이터 확인
        final_saved_data = redis_client.hgetall(f"job:{job_id}")
        logger.info(f"Final saved Redis data: {final_saved_data}")

        return {
            "status": JobStatus.COMPLETED,
            "summary": result["summary"],
            "checklist": result["checklist"]
        }

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.result = json.dumps({"error": str(e)})
                try:
                    db.commit()
                except Exception as db_e:
                    logger.error(f"DB error: {db_e}")
        except Exception as db_outer:
            logger.error(f"Outer DB error: {db_outer}")
        try:
            redis_client.hset(f"job:{job_id}", mapping={
                "status": JobStatus.FAILED,
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            })
        except Exception as re:
            logger.error(f"Redis error: {re}")
    finally:
        db.close()
        logger.info(f"Job processing finished: {job_id}") 