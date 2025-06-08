from celery import Celery
from app.core.config import settings
import os

# 환경 변수에서 Redis URL 가져오기
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

celery_app = Celery(
    "worker",
    broker=broker_url,
    backend=result_backend,
    include=['app.tasks.process_guideline']  # 태스크 모듈 명시적 포함
)

# 태스크 라우팅 설정
celery_app.conf.task_routes = {
    "app.tasks.process_guideline.process_guideline": {"queue": "main-queue"}  # 전체 경로로 수정
}

# 태스크 설정
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    result_expires=3600,  # 1시간
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_queue_max_priority=10,
    task_default_priority=5,
    worker_prefetch_multiplier=1,
    worker_concurrency=1,  # 동시 작업 수 제한
    task_track_started=True,  # 작업 시작 추적
    task_time_limit=3600,  # 작업 시간 제한 (1시간)
    task_soft_time_limit=3000  # 소프트 시간 제한 (50분)
) 