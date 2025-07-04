from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi_health import health

from database.checkpointer import create_checkpointer_pool

from utils.logger import Logger

logger = Logger("health")

# 1. App/server check (always returns True for basic up signal)
async def app_check() -> bool:
    logger.info("Checking app connection")
    return True

# 2. DB check (verifies connection is alive and usable)
async def db_check() -> bool:
    logger.info("Checking database connection")
    try:
        pool = create_checkpointer_pool()
        await pool.open(wait=True)
        async with pool.connection() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.warning(f"[DB CHECK FAILED]: {e}")
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

# Combine both checks into one endpoint
health_endpoint = health(
    [app_check, db_check],
    success_handler=success_handler,
    failure_handler=failure_handler,
)

router = APIRouter()
router.add_api_route("/health", health_endpoint, methods=["GET"])
