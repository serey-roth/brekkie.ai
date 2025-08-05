from typing import Any, Dict, cast

from services.redis.redis_client import RedisClient

from schemas.chat_session_data_stream import ChatSessionDataStreamEntry

from utils.logger import Logger

logger = Logger("chat_session_data_stream_writer")

class ChatSessionDataStreamWriter:
    """Service for writing data to the Redis stream for chat session data"""

    def __init__(self, stream: str, redis_client: RedisClient):
        self.redis_client = redis_client
        self.stream = stream

    async def add_entry(self, entry: ChatSessionDataStreamEntry) -> str:
        """Add an entry to the stream."""
        entry_id = await self.redis_client.xadd(
            self.stream, {"type": entry.type.value, "payload": entry.payload.model_dump_json()}
        )
        return cast(str, entry_id)

    async def get_stream_info(self) -> Dict[str, Any]:
        """Get information about the stream."""
        try:
            info = await self.redis_client.xinfo_stream(self.stream)
            return info if info is not None and isinstance(info, dict) else {}
        except Exception as e:
            logger.error(f"Error getting stream info: {e}")
            return {}

    async def get_stream_length(self) -> int:
        """Get the number of entries in the stream."""
        try:
            length = await self.redis_client.xlen(self.stream)
            return length if length is not None and isinstance(length, int) else 0
        except Exception as e:
            logger.error(f"Error getting stream length: {e}")
            return 0
