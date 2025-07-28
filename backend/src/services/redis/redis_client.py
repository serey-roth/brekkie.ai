import redis.asyncio as redis
from utils.logger import Logger

logger = Logger("redis_client")


RedisClient = redis.Redis


def create_redis_client(redis_url: str) -> RedisClient:
    try:
        client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis client created successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to create Redis client: {e}")
        raise e
