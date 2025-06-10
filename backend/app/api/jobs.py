from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.job import Job
from app.core.celery_app import celery_app
from fastapi.responses import StreamingResponse
import uuid
import json
import asyncio
import logging
import os
import shutil
from redis import Redis
from app.core.config import settings
from datetime import datetime
import aiofiles
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis 연결 풀 생성
redis_pool = None

def get_redis():
    global redis_pool
    if redis_pool is None:
        redis_pool = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_timeout=1,
            socket_connect_timeout=1
        )
    return redis_pool

async def save_file_async(file_path: str, file: UploadFile):
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

async def create_job_in_db(job_id: str, db: Session):
    job = Job(id=job_id, status="pending")
    db.add(job)
    db.commit()
    return job

@router.post("/jobs")
async def create_job(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 파일 확장자 검증
    allowed_extensions = {".pdf", ".docx", ".doc", ".txt"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, DOC, or TXT files are allowed")
    
    # 작업 ID 생성
    job_id = str(uuid.uuid4())
    
    # uploads 디렉토리가 없으면 생성
    os.makedirs("uploads", exist_ok=True)
    
    # 고유한 파일명 생성
    unique_filename = f"{job_id}_{file.filename}"
    file_path = f"uploads/{unique_filename}"
    
    # 비동기로 파일 저장 및 DB 작업 실행
    await save_file_async(file_path, file)
    await create_job_in_db(job_id, db)
    
    # Celery 작업 등록
    celery_app.send_task(
        "app.tasks.process_guideline.process_guideline",
        args=[job_id, unique_filename],
        task_id=job_id
    )
    
    return {"jobId": job_id, "status": "pending"}

@router.get("/jobs/{event_id}")
async def get_job_status(
    event_id: str,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == event_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "jobId": job.id,
        "status": job.status,
        "createdAt": job.created_at,
        "updatedAt": job.updated_at,
        "result": job.result
    }

@router.get("/jobs/{event_id}/stream")
async def stream_job_status(
    event_id: str,
    db: Session = Depends(get_db)
):
    async def event_generator():
        while True:
            job = db.query(Job).filter(Job.id == event_id).first()
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            
            data = {
                "id": job.id,
                "status": job.status,
                "createdAt": job.created_at.isoformat() if job.created_at else None,
                "updatedAt": job.updated_at.isoformat() if job.updated_at else None,
                "result": job.result
            }
            
            yield f"data: {json.dumps(data)}\n\n"
            
            if job.status in ["completed", "failed"]:
                break
                
            await asyncio.sleep(2)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    ) 

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching job status for job_id: {job_id}")
    
    # Redis에서 먼저 확인
    job_data = get_redis().hgetall(f"job:{job_id}")
    if job_data:
        logger.info(f"Retrieved Redis data: {job_data}")
        
        # JSON 문자열을 파싱
        summary = job_data.get("summary", None)
        checklist = None
        if job_data.get("checklist"):
            try:
                checklist = json.loads(job_data["checklist"])
            except Exception as e:
                checklist = [job_data["checklist"]]
        
        # 파일명에서 job_id 제거
        filename = job_data.get("filename", "")
        if filename and filename.startswith(f"{job_id}_"):
            filename = filename[len(job_id) + 1:]
        
        return {
            "jobId": job_id,
            "status": job_data.get("status", "pending"),
            "filename": filename,
            "summary": summary,
            "checklist": checklist,
            "started_at": job_data.get("started_at"),
            "completed_at": job_data.get("completed_at"),
            "failed_at": job_data.get("failed_at"),
            "error": job_data.get("error")
        }
    
    # Redis에 없으면 DB에서 확인
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.error(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "jobId": job.id,
        "status": job.status,
        "createdAt": job.created_at,
        "updatedAt": job.updated_at,
        "result": job.result
    } 