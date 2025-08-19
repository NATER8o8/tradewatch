
from .config import env
import redis

def get_redis():
    url = env("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(url)
