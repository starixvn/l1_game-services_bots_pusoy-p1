from src.celery import celery_worker
from src.celery.celery_broker import celery_app

from fastapi import Request
from fastapi.responses  import JSONResponse
from fastapi.encoders import jsonable_encoder
from app_queue import router



@router.get("/")
async def read_root():
    return {"message": "Welcome to Justin!"}


@router.post("/move")
async def get_move(request_card: Request) -> JSONResponse:
    formated_request = await request_card.json()
    private_input = formated_request['private']['input']
    best_arrangement = router.state.redis_instance.get(private_input)
    
    if best_arrangement is None or celery_app.AsyncResult(best_arrangement).ready():
        task = celery_worker.process_move.apply_async(args=[router.state.pusoy_bot, formated_request])
        best_arrangement = task.get()
        router.state.redis_instance.set(private_input, best_arrangement)
        
    return JSONResponse(
        content=jsonable_encoder(best_arrangement),
        status_code=200
    )



@router.post("/suggest") 
async def get_suggest(request_card: Request) -> JSONResponse:
    formated_request = await request_card.json()
    private_input = formated_request['private']['input']
    best_arrangement = router.state.redis_instance.get(private_input)
    
    if best_arrangement is None or celery_app.AsyncResult(best_arrangement).ready():
        task = celery_worker.process_suggest.apply_async(args=[router.state.pusoy_bot, formated_request])
        best_arrangement = task.get()
        router.state.redis_instance.set(private_input, best_arrangement)
        
    return JSONResponse(
        content=jsonable_encoder(best_arrangement),
        status_code=200
    )
