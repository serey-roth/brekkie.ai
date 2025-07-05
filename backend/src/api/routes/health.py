from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from fastapi_health import health

from utils.logger import Logger

logger = Logger("health")

# Dependency to get the checkpointer pool
async def get_checkpointer_pool(request: Request):
    return request.app.state.checkpointer_db_pool

# Dependency to get the Redis client
async def get_redis_client(request: Request):
    return request.app.state.redis_client

# 1. App/server check (always returns True for basic up signal)
async def app_check() -> bool:
    logger.info("Checking app connection")
    return True

# 2. DB check (verifies connection is alive and usable)
async def db_check(pool=Depends(get_checkpointer_pool)) -> bool:
    logger.info("Checking database connection")
    try:
        async with pool.connection(timeout=2) as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.warning(f"[DB CHECK FAILED]: {e}")
        return False

# 3. Redis check (verifies Redis connection is alive and usable)
async def redis_check(redis_client=Depends(get_redis_client)) -> bool:
    logger.info("Checking Redis connection")
    try:
        await redis_client.ping()
        return True
    except Exception as e:
        logger.warning(f"[REDIS CHECK FAILED]: {e}")
        return False

async def success_handler(**kwargs):
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "brekkie-ai",
            "checks": kwargs,  # This shows which checks passed
        },
    )

async def failure_handler(**kwargs):
    return JSONResponse(
        status_code=503,
        content={
            "status": "unhealthy",
            "service": "brekkie-ai",
            "checks": kwargs,  # This shows which check(s) failed
        },
    )

# Combine all checks into one endpoint
health_endpoint = health(
    [app_check, db_check, redis_check],
    success_handler=success_handler,
    failure_handler=failure_handler,
)

router = APIRouter()
router.add_api_route("/health", health_endpoint, methods=["GET"])
