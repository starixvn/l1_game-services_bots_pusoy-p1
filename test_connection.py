# from src.celery import celery_worker
# from src.celery.celery_broker import celery_app

# request = {
#   "private": {
#     "input": [1, 4, 11, 46, 45, 14, 19, 17, 42, 37, 29, 39, 40],
#     "player_id": "",
#     "arrangement_id": "",
#     "input_hash": 0
#   },
#   "shared": {
#     "match": {
#       "id": ""
#     }
#   }
# }

# res = celery_worker.process_suggest.delay(request)
# print(res.status)

import redis

def check_redis_connection(redis_host, redis_port, redis_password):
    try:
        # Create a Redis connection
        redis_client = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True
        )

        # Ping the Redis server
        if redis_client.ping():
            print("Successfully connected to Redis!")
        else:
            print("Failed to connect to Redis.")
    except redis.ConnectionError as e:
        print(f"Redis connection error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Parameters for Redis connection
redis_host = '10.18.200.131'
redis_port = 16379
redis_password = "foo1@bared"

# Check the connection
check_redis_connection(redis_host, redis_port, redis_password)