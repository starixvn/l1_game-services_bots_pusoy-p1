from celery_broker import celery_app
import json
from main import move_v1, suggest_v1

from src.service.algorithm import PusoyBot


pusoy_bot = PusoyBot()



@celery_app.task
def process(formated_request, func_option):
    
    if isinstance(formated_request, str):
        formated_request = json.loads(formated_request)
    
    func_serialized = {
        'suggest': suggest_v1,
        'move': move_v1
    }
        
    output = func_serialized[func_option](pusoy_bot, formated_request['private']['input'])
    output['player_id'] = formated_request['private']['player_id']
    output['arrangement_id'] = formated_request['private']['arrangement_id']
    output['input_hash'] = formated_request['private']['input_hash']

    return output
