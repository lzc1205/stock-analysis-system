"""
Redis 缓存管理
"""
import redis
from app.config import settings

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password or None,
    db=settings.redis_db,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True,
)


def get_cache() -> redis.Redis:
    return redis_client


def cache_get(key: str) -> str | None:
    try:
        return redis_client.get(key)
    except redis.RedisError:
        return None


def cache_set(key: str, value: str, expire: int = 3600) -> bool:
    try:
        redis_client.setex(key, expire, value)
        return True
    except redis.RedisError:
        return False


def cache_delete(key: str) -> bool:
    try:
        redis_client.delete(key)
        return True
    except redis.RedisError:
        return False