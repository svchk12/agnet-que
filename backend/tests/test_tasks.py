import pytest
from app.tasks.process_guideline import process_guideline
from app.models.job import Job, JobStatus
from app.core.database import SessionLocal
import json
import os
import shutil
from datetime import datetime
from reportlab.pdfgen import canvas
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
import docx

# awaitable 유틸 함수 추가
def awaitable(result):
    async def _awaitable(*args, **kwargs):
        return result
    return _awaitable()

@pytest.fixture
def mock_redis(mocker):
    """Redis 클라이언트 모킹"""
    mock_redis = mocker.patch('app.tasks.process_guideline.redis_client')
    mock_redis.hgetall.return_value = {
        "status": JobStatus.COMPLETED,
        "summary": "Test summary",
        "checklist": json.dumps(["Test item 1", "Test item 2"])
    }
    return mock_redis

@pytest.fixture
def mock_agent(mocker):
    """Agent 서버 호출 모킹"""
    # create_agent_session 모킹
    mocker.patch('app.tasks.process_guideline.create_agent_session', return_value="test-session-id")
    
    # process_with_agent 모킹
    mocker.patch('app.tasks.process_guideline.process_with_agent', return_value={
        "summary": "Test summary",
        "checklist": ["Test item 1", "Test item 2"]
    })
    
    return None

@pytest.fixture
def test_pdf_file(tmp_path):
    """테스트용 PDF 파일 생성"""
    # uploads 디렉토리 생성
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    # PDF 파일 생성
    pdf_path = os.path.join(uploads_dir, "test_guideline.pdf")
    
    # reportlab을 사용하여 PDF 생성
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Test PDF Content")
    c.save()
    
    # PDF 파일 저장
    with open(pdf_path, "wb") as f:
        f.write(buffer.getvalue())
    
    return pdf_path

@pytest.fixture
def db_session():
    """데이터베이스 세션 fixture"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_process_guideline_task(mock_redis, mock_agent, test_pdf_file, db_session):
    """가이드라인 처리 작업 테스트"""
    job_id = "test-job-id-1"
    
    # 테스트용 Job 생성
    job = Job(id=job_id, status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()
    
    try:
        # 작업 실행
        process_guideline(job_id, os.path.basename(test_pdf_file))
        
        # Redis에 상태가 저장되었는지 확인
        mock_redis.hset.assert_any_call(
            f"job:{job_id}",
            mapping={
                "status": JobStatus.PROCESSING,
                "filename": os.path.basename(test_pdf_file),
                "started_at": mock_redis.hset.call_args_list[0][1]["mapping"]["started_at"],
                "summary": "",
                "checklist": "[]"
            }
        )
        
        # 작업 상태가 업데이트되었는지 확인
        updated_job = db_session.query(Job).filter(Job.id == job_id).first()
        assert updated_job.status == JobStatus.COMPLETED
        assert "summary" in updated_job.result
        assert "checklist" in updated_job.result
    finally:
        # 테스트 데이터 정리
        db_session.query(Job).filter(Job.id == job_id).delete()
        db_session.commit()
        if os.path.exists(test_pdf_file):
            os.remove(test_pdf_file)

def test_process_guideline_invalid_file(mock_redis, db_session):
    """잘못된 파일 처리 테스트"""
    job_id = "test-job-id-2"
    filename = "nonexistent.pdf"
    
    # 테스트용 Job 생성
    job = Job(id=job_id, status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()
    
    try:
        # 작업 실행
        process_guideline(job_id, filename)
        
        # 에러 상태가 Redis에 저장되었는지 확인
        mock_redis.hset.assert_any_call(
            f"job:{job_id}",
            mapping={
                "status": JobStatus.FAILED,
                "error": "File not found",
                "failed_at": mock_redis.hset.call_args_list[-1][1]["mapping"]["failed_at"]
            }
        )
        
        # 작업 상태가 업데이트되었는지 확인
        updated_job = db_session.query(Job).filter(Job.id == job_id).first()
        assert updated_job.status == JobStatus.FAILED
    finally:
        # 테스트 데이터 정리
        db_session.query(Job).filter(Job.id == job_id).delete()
        db_session.commit()

def test_process_guideline_agent_error(mock_redis, test_pdf_file, db_session, mocker):
    """Agent 서버 에러 처리 테스트"""
    job_id = "test-job-id-3"
    # process_with_agent가 예외를 발생시키도록 모킹
    mocker.patch('app.tasks.process_guideline.process_with_agent', side_effect=Exception("Agent Error"))

    # 테스트용 Job 생성
    job = Job(id=job_id, status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()

    try:
        # 작업 실행
        process_guideline(job_id, os.path.basename(test_pdf_file))

        # 작업 상태가 FAILED로 업데이트되었는지 확인
        updated_job = db_session.query(Job).filter(Job.id == job_id).first()
        assert updated_job.status == JobStatus.FAILED
        assert "error" in updated_job.result
    finally:
        # 테스트 데이터 정리
        db_session.query(Job).filter(Job.id == job_id).delete()
        db_session.commit()
        if os.path.exists(test_pdf_file):
            os.remove(test_pdf_file)

def test_process_guideline_non_pdf_file(mock_redis, mock_agent, db_session):
    """PDF가 아닌 파일 처리 테스트"""
    job_id = "test-job-id-4"
    
    # 테스트용 Job 생성
    job = Job(id=job_id, status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()
    
    try:
        # 작업 실행
        process_guideline(job_id, "test.txt")
        
        # 작업 상태가 FAILED로 업데이트되었는지 확인
        updated_job = db_session.query(Job).filter(Job.id == job_id).first()
        assert updated_job.status == JobStatus.FAILED
        assert "error" in updated_job.result
    finally:
        # 테스트 데이터 정리
        db_session.query(Job).filter(Job.id == job_id).delete()
        db_session.commit()

def test_process_guideline_file_extraction_error(mock_redis, mock_agent, test_pdf_file, db_session, mocker):
    """파일 내용 추출 실패 테스트"""
    job_id = "test-job-id-5"
    
    # extract_text_from_file 함수가 예외를 발생시키도록 모킹
    mocker.patch('app.tasks.process_guideline.extract_text_from_file', side_effect=Exception("File extraction failed"))
    
    # 테스트용 Job 생성
    job = Job(id=job_id, status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()
    
    try:
        # 작업 실행
        process_guideline(job_id, os.path.basename(test_pdf_file))
        
        # 작업 상태가 FAILED로 업데이트되었는지 확인
        updated_job = db_session.query(Job).filter(Job.id == job_id).first()
        assert updated_job.status == JobStatus.FAILED
        assert "error" in updated_job.result
    finally:
        # 테스트 데이터 정리
        db_session.query(Job).filter(Job.id == job_id).delete()
        db_session.commit()

def test_process_guideline_redis_error(mock_agent, test_pdf_file, db_session, mocker):
    """Redis 연결 실패 테스트"""
    job_id = "test-job-id-6"
    
    # redis_client 모킹
    mock_redis = mocker.patch('app.tasks.process_guideline.redis_client')
    mock_redis.hset.side_effect = Exception("Redis connection failed")
    mock_redis.hgetall.return_value = {}  # 빈 딕셔너리 반환
    
    # 테스트용 Job 생성
    job = Job(id=job_id, status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()
    
    try:
        # 작업 실행
        process_guideline(job_id, os.path.basename(test_pdf_file))
        
        # 작업 상태가 FAILED로 업데이트되었는지 확인
        updated_job = db_session.query(Job).filter(Job.id == job_id).first()
        assert updated_job.status == JobStatus.FAILED
        assert "error" in updated_job.result
    finally:
        # 테스트 데이터 정리
        db_session.query(Job).filter(Job.id == job_id).delete()
        db_session.commit()

def test_process_guideline_db_error(mock_redis, mock_agent, test_pdf_file, db_session, mocker):
    """데이터베이스 에러 테스트"""
    job_id = "test-job-id-7"

    # 혹시 남아있는 job이 있으면 미리 삭제
    db_session.query(Job).filter(Job.id == job_id).delete()
    db_session.commit()

    # 테스트용 Job 생성 및 실제 커밋
    job = Job(id=job_id, status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()

    # 이후 커밋만 예외를 발생시키도록 모킹
    mocker.patch.object(db_session, 'commit', side_effect=Exception("Database error"))
    mocker.patch('app.tasks.process_guideline.SessionLocal', return_value=db_session)

    try:
        process_guideline(job_id, os.path.basename(test_pdf_file))
        updated_job = db_session.query(Job).filter(Job.id == job_id).first()
        # DB 커밋이 실패했으므로 status는 여전히 PENDING이어야 함
        assert updated_job.status == JobStatus.PENDING
        # DB 커밋이 실패했으므로 result는 None이어야 함
        assert updated_job.result is None
    finally:
        try:
            db_session.rollback()
            db_session.query(Job).filter(Job.id == job_id).delete()
            db_session.commit()
        except Exception:
            db_session.rollback()

def test_process_guideline_empty_file(mock_redis, mock_agent, db_session, mocker):
    """빈 파일 처리 테스트"""
    job_id = "test-job-id-8"
    
    # 빈 PDF 파일 생성
    empty_pdf_path = "uploads/empty.pdf"
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.save()
    
    with open(empty_pdf_path, "wb") as f:
        f.write(buffer.getvalue())
    
    # 테스트용 Job 생성
    job = Job(id=job_id, status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()
    
    try:
        # extract_text_from_file이 빈 문자열을 반환하도록 모킹
        mocker.patch('app.tasks.process_guideline.extract_text_from_file', return_value="")
        
        # process_with_agent가 예외를 발생시키도록 모킹
        mocker.patch('app.tasks.process_guideline.process_with_agent', side_effect=Exception("Empty file"))
        
        # 작업 실행
        process_guideline(job_id, "empty.pdf")
        
        # 작업 상태가 FAILED로 업데이트되었는지 확인
        updated_job = db_session.query(Job).filter(Job.id == job_id).first()
        assert updated_job.status == JobStatus.FAILED
        assert "error" in updated_job.result
    finally:
        # 테스트 데이터 정리
        db_session.query(Job).filter(Job.id == job_id).delete()
        db_session.commit()
        if os.path.exists(empty_pdf_path):
            os.remove(empty_pdf_path)

def test_process_guideline_doc_file(mock_redis, mock_agent, db_session, mocker):
    """DOC/DOCX 파일 처리 테스트"""
    job_id = "test-job-id-9"
    
    # 테스트용 DOCX 파일 생성
    docx_path = "uploads/test_guideline.docx"
    doc = docx.Document()
    doc.add_paragraph("Test DOCX Content")
    doc.save(docx_path)
    
    # 테스트용 Job 생성
    job = Job(id=job_id, status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()
    
    try:
        # 작업 실행
        process_guideline(job_id, "test_guideline.docx")
        
        # 작업 상태가 COMPLETED로 업데이트되었는지 확인
        updated_job = db_session.query(Job).filter(Job.id == job_id).first()
        assert updated_job.status == JobStatus.COMPLETED
        assert "summary" in updated_job.result
        assert "checklist" in updated_job.result
    finally:
        # 테스트 데이터 정리
        db_session.query(Job).filter(Job.id == job_id).delete()
        db_session.commit()
        if os.path.exists(docx_path):
            os.remove(docx_path)

def test_process_guideline_txt_file(mock_redis, mock_agent, db_session, mocker):
    """TXT 파일 처리 테스트"""
    job_id = "test-job-id-10"
    
    # 테스트용 TXT 파일 생성
    txt_path = "uploads/test_guideline.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Test TXT Content")
    
    # 테스트용 Job 생성
    job = Job(id=job_id, status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()
    
    try:
        # 작업 실행
        process_guideline(job_id, "test_guideline.txt")
        
        # 작업 상태가 COMPLETED로 업데이트되었는지 확인
        updated_job = db_session.query(Job).filter(Job.id == job_id).first()
        assert updated_job.status == JobStatus.COMPLETED
        assert "summary" in updated_job.result
        assert "checklist" in updated_job.result
    finally:
        # 테스트 데이터 정리
        db_session.query(Job).filter(Job.id == job_id).delete()
        db_session.commit()
        if os.path.exists(txt_path):
            os.remove(txt_path)

def test_process_guideline_agent_events(mock_redis, test_pdf_file, db_session, mocker):
    """에이전트 이벤트 처리 테스트"""
    job_id = "test-job-id-11"
    
    # create_agent_session과 process_with_agent를 모두 모킹
    mocker.patch('app.tasks.process_guideline.create_agent_session', return_value="test-session-id")
    mocker.patch('app.tasks.process_guideline.process_with_agent', return_value={
        "summary": "Test Summary",
        "checklist": ["Test Item 1", "Test Item 2"]
    })
    
    # 테스트용 Job 생성
    job = Job(id=job_id, status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()
    
    try:
        # 작업 실행
        process_guideline(job_id, os.path.basename(test_pdf_file))
        
        # 작업 상태가 COMPLETED로 업데이트되었는지 확인
        updated_job = db_session.query(Job).filter(Job.id == job_id).first()
        assert updated_job.status == JobStatus.COMPLETED
        result = updated_job.result
        assert result["summary"] == "Test Summary"
        assert result["checklist"] == ["Test Item 1", "Test Item 2"]
    finally:
        # 테스트 데이터 정리
        db_session.query(Job).filter(Job.id == job_id).delete()
        db_session.commit() 