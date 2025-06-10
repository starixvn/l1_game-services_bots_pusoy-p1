from celery import Celery

from src.utils.constant import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

# Initialize Celery
celery_app = Celery(
    __name__,
    broker=CELERY_BROKER_URL, 
    backend=CELERY_RESULT_BACKEND
)