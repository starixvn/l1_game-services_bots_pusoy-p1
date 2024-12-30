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




app = FastAPI(
    title='Pusoy', 
    version='0.0.1',
    root_path='/api/v1',
    root_path_in_servers=False,
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
    best_arrangement = process(formated_request, 'move')

    return JSONResponse(
        content=jsonable_encoder(best_arrangement),
        status_code=200
    )



@app.post("/suggest") 
async def get_suggest(request_card: Request) -> JSONResponse:
    formated_request = await request_card.json()
    private_input = formated_request['private']['input']    
    best_arrangement = process(formated_request, 'suggest')
    
    return JSONResponse(
        content=jsonable_encoder(best_arrangement),
        status_code=200
    )


#app.include_router(router=router, prefix='/api/v1')


if __name__ == "__main__":
    uvicorn.run(
        app='app:app', 
        host=APP_HOST, 
        port=APP_PORT, 
        log_level='info'
    )
