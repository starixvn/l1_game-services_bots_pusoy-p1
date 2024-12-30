import os
import logging
import psutil
import uvicorn
import warnings
import json

warnings.filterwarnings(action='ignore')


from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


from redis import Redis

from src.utils.constant import ALLOW_ORIGINS, APP_HOST, APP_PORT
from endpoint_filter import EndpointFilter

from main import process

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
    root_path='/api/v1',
    root_path_in_servers=False,
    lifespan=lifespan
)
#router = APIRouter(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to Justin!"}


@app.post("/move")
async def get_move(request_card: Request) -> JSONResponse:
    formated_request = await request_card.json()
    private_input = formated_request['private']['input']
    best_arrangement = app.state.redis_instance.get(str(private_input))

    
    if best_arrangement is None:
        best_arrangement = process(formated_request, 'move')

        app.state.redis_instance.set(str(private_input), json.dumps(best_arrangement), ex=60)
        
    else:
        best_arrangement = json.loads(best_arrangement.decode('utf-8'))
        print(f'{best_arrangement} is already in Redis with key {private_input}')
        
    return JSONResponse(
        content=jsonable_encoder(best_arrangement),
        status_code=200
    )



@app.post("/suggest") 
async def get_suggest(request_card: Request) -> JSONResponse:
    formated_request = await request_card.json()
    private_input = formated_request['private']['input']
    best_arrangement = app.state.redis_instance.get(str(private_input))
    
    if best_arrangement is None:
        best_arrangement = process(formated_request, 'suggest')

        app.state.redis_instance.set(str(private_input), json.dumps(best_arrangement), ex=60)
    
    else:
        best_arrangement = json.loads(best_arrangement.decode('utf-8'))
        print(f'{best_arrangement} is already in Redis with key {private_input}')
    
    return JSONResponse(
        content=jsonable_encoder(best_arrangement),
        status_code=200
    )


#app.include_router(router=router, prefix='/api/v1')


if __name__ == "__main__":

    print("The number of CPU cores is:", psutil.cpu_count(logical=False) - 2)
    uvicorn.run(
        app='app:app', 
        host=APP_HOST, 
        port=APP_PORT, 
        workers=psutil.cpu_count(logical=False) - 2
    )
