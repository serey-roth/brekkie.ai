import os
import redis.asyncio as redis

from dotenv import load_dotenv

# Load environment variables with proper precedence
load_dotenv()  # Load .env if it exists
load_dotenv(".env.local")  # Load .env.local (development)

from utils.logger import Logger

logger = Logger('redis_client')

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

_redis_client: redis.Redis | None = None

RedisClient = redis.Redis


def get_redis_client() -> RedisClient:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        except Exception as e:
            logger.error(f"Failed to create Redis client: {e}")
            raise e
    return _redis_client