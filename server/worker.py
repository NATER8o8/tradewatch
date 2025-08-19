
from rq import Worker
from .tasks import get_queue
from .redis_client import get_redis

if __name__ == "__main__":
    r = get_redis()
    q = get_queue()
    Worker([q.name], connection=r).work(with_scheduler=True)
