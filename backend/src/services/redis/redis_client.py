import os
import redis.asyncio as redis

from dotenv import load_dotenv

# Load environment variables with proper precedence
load_dotenv()  # Load .env if it exists
load_dotenv(".env.local")  # Load .env.local (development)

from utils.logger import Logger

logger = Logger('redis_client')

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

RedisClient = redis.Redis

def create_redis_client() -> RedisClient:
    try:
        client = redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis client created successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to create Redis client: {e}")
        raise e