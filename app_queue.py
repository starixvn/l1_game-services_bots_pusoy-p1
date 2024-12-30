import os
import logging
import psutil
import uvicorn
import warnings

warnings.filterwarnings(action='ignore')


from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import dill
from redis import Redis

from src.utils.constant import ALLOW_ORIGINS, APP_HOST, APP_PORT
from endpoint_filter import EndpointFilter

from src.celery import celery_worker
from src.celery.celery_broker import celery_app

from fastapi import Request
from fastapi.responses  import JSONResponse
from fastapi.encoders import jsonable_encoder


uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.addFilter(EndpointFilter(path="/"))



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator:

    redis_instance = Redis.from_url(os.getenv("CELERY_BROKER_URL"))
    response = redis_instance.ping()
    if response:
        print("Connected to Redis!")
    app.state.redis_instance = redis_instance

    yield
    redis_instance.close()



app = FastAPI(
    title='Pusoy', 
    version='0.0.1',
    root_path_in_servers=False,
    lifespan=lifespan
)
router = APIRouter(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@router.get("/")
async def read_root():
    return {"message": "Welcome to Justin!"}


@router.post("/move")
async def get_move(request_card: Request) -> JSONResponse:
    formated_request = await request_card.json()
    private_input = formated_request['private']['input']
    best_arrangement = app.state.redis_instance.get(str(private_input))

    
    if best_arrangement is None or celery_app.AsyncResult(best_arrangement).ready():
        task = celery_worker.process.delay(formated_request, 'move')
        best_arrangement = task.get()
        app.state.redis_instance.set(str(private_input), best_arrangement)
        
    return JSONResponse(
        content=jsonable_encoder(best_arrangement),
        status_code=200
    )



@router.post("/suggest") 
async def get_suggest(request_card: Request) -> JSONResponse:
    formated_request = await request_card.json()
    private_input = formated_request['private']['input']
    best_arrangement = app.state.redis_instance.get(str(private_input))
    
    
    if best_arrangement is None or celery_app.AsyncResult(best_arrangement).ready():
        task = celery_worker.process.delay(formated_request, 'suggest')
        best_arrangement = task.get()
        app.state.redis_instance.set(private_input, best_arrangement)
        
    return JSONResponse(
        content=jsonable_encoder(best_arrangement),
        status_code=200
    )


app.include_router(router=router, prefix='/api/v1')


if __name__ == "__main__":

    print("The number of CPU cores is:", psutil.cpu_count(logical=False) - 2)
    uvicorn.run(
        app='app_caching:app', 
        host=APP_HOST, 
        port=APP_PORT, 
        workers=psutil.cpu_count(logical=False) - 2,
        reload=True
    )
