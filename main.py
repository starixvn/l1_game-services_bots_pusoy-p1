import time
import json
from src.service.preprocessing import PreProcessing
from src.service.postprocessing import PostProcessing

from src.service.algorithm import PusoyBot

pusoy_bot = PusoyBot()

def move_v1(pusoy_bot, list_card_value) -> dict:
    # Preprocess the input
    input = PreProcessing(list_card_value).preprocessing_input()

    # Run the algorithm
    pusoy_bot.board = input
    best_arrangement = pusoy_bot.get_best_arrangement()

    # Postprocess the output
    output = PostProcessing(list_card_value, best_arrangement).postprocessing_output()
    return output

def suggest_v1(pusoy_bot, list_card_value) -> dict:
    # Preprocess the input
    input = PreProcessing(list_card_value).preprocessing_input()

    # Run the algorithm
    pusoy_bot.board = input
    list_best_arrangement = pusoy_bot.get_top_k_back_mid_front_type_arrangements(k=16)

    # Postprocess the output
    output = PostProcessing(list_card_value, list_best_arrangement).postprocessing_output()
    return output

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

if __name__ == "__main__":
    start_time = time.time()

    import numpy as np
    import tracemalloc

    tracemalloc.start()

    list_time = []
    for i in range(10):
        full_deck = list(range(52))
        np.random.shuffle(full_deck)
        list_card_value = full_deck[:13]
        start_time_algo = time.time()
        output = suggest_v1(list_card_value)
        end_time_algo = time.time()
        list_time.append(end_time_algo - start_time_algo)
    print("Average time: ", np.mean(list_time))
    current, peak = tracemalloc.get_traced_memory()
    print('Current and peak memory usage: {}[MB] {}[MB]'.format(current/(1024*1024), peak/(1024*1024)))
    tracemalloc.stop()

    end_time = time.time()
    print("Elapsed time: ", end_time - start_time)         