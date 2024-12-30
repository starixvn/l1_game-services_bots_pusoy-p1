#!/bin/bash

# Redis Configuration
export REDIS_HOST="10.18.200.131"
export REDIS_PORT="16379"
export REDIS_PASSWORD="foo1@bared"

# Celery Configuration
export CELERY_BROKER_URL="redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/0"
export CELERY_RESULT_BACKEND="redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/0"

# FastAPI Configuration
export APP_HOST="0.0.0.0"
export APP_PORT="80"

# Celery Worker Configuration
export CELERY_WORKER_LOGLEVEL="info"

# Miscellaneous
export ALLOW_ORIGINS="*"

python app.py
# celery -A celery_worker.celery_app flower --loglevel=info
