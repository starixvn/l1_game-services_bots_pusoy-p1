import os

# FastAPI Configuration
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 5000))

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

# Allowed Origins
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")

# Redis Configuration
REDIS_TASK_KEY = "current_task"