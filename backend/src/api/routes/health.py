from fastapi import APIRouter
from utils.logger import Logger

router = APIRouter()
logger = Logger("health")

@router.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "healthy", "service": "brekkie-ai"} 