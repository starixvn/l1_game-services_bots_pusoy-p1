#!/bin/bash

# FastAPI Configuration
export APP_HOST="0.0.0.0"
export APP_PORT="5000"

# Miscellaneous
export ALLOW_ORIGINS="*"

python app.py
# celery -A celery_worker.celery_app flower --loglevel=info
