from app.core.celery_app import celery_app
import logging
from app.tasks.process_guideline import process_guideline  # 태스크 모듈 명시적 임포트

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 태스크 모듈 등록
celery_app.autodiscover_tasks(['app.tasks'])

if __name__ == "__main__":
    celery_app.start() 