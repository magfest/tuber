import os

import redis
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

worker_conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(worker_conn):
        worker = Worker(map(Queue, listen))
        worker.work()