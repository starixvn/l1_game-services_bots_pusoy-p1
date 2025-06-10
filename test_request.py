import numpy as np
import requests
import json
import threading
import time

def test(n_iter):
    start_time = time.time()
    for i in range(n_iter):
        full_deck = list(range(52))
        np.random.shuffle(full_deck)
        list_card_value = full_deck[:13]
        url = "http://localhost:80/api/v1/move"
        data = {
            "private": {
                "input": list_card_value,
                "player_id": "",
                "arrangement_id": "",
                "input_hash": 0
            },
            "shared": {
                "match": {
                    "id": ""
                }
            }
        }
        response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
        response_json = response.json() if response.status_code == 200 else None
        print(f"status_code: {response.status_code}, time: {time.time() - start_time}")

if __name__ == "__main__":
    n_threads = 20
    threads = []

    # Tạo và khởi chạy các thread
    for i in range(n_threads):
        print(f"Running thread {i}")
        thread = threading.Thread(target=test, args=(100,))
        thread.start()
        threads.append(thread)

    # Đợi cho tất cả các thread kết thúc
    for thread in threads:
        thread.join()