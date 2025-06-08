import pytest
from fastapi.testclient import TestClient
import time
import uuid
import io

def test_create_job(client, test_pdf_file):
    """작업 생성 테스트"""
    with open(test_pdf_file, "rb") as f:
        response = client.post(
            "/jobs",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "jobId" in data
    assert "status" in data
    assert data["status"] == "pending"

def test_create_job_invalid_file_type(client):
    """잘못된 파일 타입으로 작업 생성 시도"""
    response = client.post(
        "/jobs",
        files={"file": ("test.txt", b"invalid content", "text/plain")}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are allowed"

def test_get_job_status(client, test_pdf_file):
    """작업 상태 조회 테스트"""
    # 작업 생성
    with open(test_pdf_file, "rb") as f:
        create_response = client.post(
            "/jobs",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    
    job_id = create_response.json()["jobId"]
    
    # 상태 조회
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert "jobId" in data
    assert "status" in data

def test_get_nonexistent_job(client):
    """존재하지 않는 작업 조회 시도"""
    response = client.get(f"/jobs/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"

def test_job_response_time(client, test_pdf_file):
    """작업 생성 응답 시간 테스트"""
    with open(test_pdf_file, "rb") as f:
        start_time = time.time()
        response = client.post(
            "/jobs",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
        end_time = time.time()
    
    assert response.status_code == 200
    assert end_time - start_time < 0.1  # 100ms 이내 응답 

def test_create_job_no_file(client):
    response = client.post("/jobs")
    assert response.status_code == 422

def test_get_job_status_not_found(client):
    response = client.get("/jobs/nonexistent-id")
    assert response.status_code == 404 