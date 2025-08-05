import asyncio
import signal

from config.settings import create_settings

from database.index import create_db_transaction_maker

from repositories.message_repository import MessageRepository
from repositories.recipe_repository import RecipeRepository
from repositories.thread_repository import ThreadRepository
from repositories.user_repository import UserRepository

from services.chat_services.chat_session_data_stream_processor import ChatSessionDataStreamProcessor
from services.data_services.message_cache_service import MessageCacheService
from services.data_services.recipe_cache_service import RecipeCacheService
from services.data_services.thread_cache_service import ThreadCacheService
from services.data_services.message_service import MessageService
from services.data_services.recipe_service import RecipeService
from services.data_services.thread_service import ThreadService
from services.redis.redis_client import create_redis_client

from utils.logger import Logger

logger = Logger("chat_session_data_stream_processor_worker")


class ChatSessionDataStreamProcessorWorker:
    """Standalone worker for running the chat session data stream processor."""
    def __init__(self):
        self.settings = create_settings()
        
        self._create_services()
        
        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)
    
    def _create_services(self):
        """Create services synchronously for signal handlers."""
        redis_client = create_redis_client(self.settings.redis_url)
        
        thread_repository = ThreadRepository()
        message_repository = MessageRepository()
        recipe_repository = RecipeRepository()
        user_repository = UserRepository()
        
        thread_cache_service = ThreadCacheService(redis_client, ttl=self.settings.thread_cache_ttl)
        message_cache_service = MessageCacheService(redis_client, ttl=self.settings.message_cache_ttl)
        recipe_cache_service = RecipeCacheService(redis_client, ttl=self.settings.recipe_cache_ttl)
        
        thread_service = ThreadService(repository=thread_repository)
        message_service = MessageService(repository=message_repository)
        recipe_service = RecipeService(repository=recipe_repository)
        
        db_transaction_maker = create_db_transaction_maker(self.settings)
        
        self.stream_processor = ChatSessionDataStreamProcessor(
            stream=self.settings.chat_session_data_stream,
            group=self.settings.chat_session_data_stream_group,
            consumer_name=self.settings.chat_session_data_stream_consumer,
            redis_client=redis_client,
            db_transaction_maker=db_transaction_maker,
            thread_cache_service=thread_cache_service,
            message_cache_service=message_cache_service,
            recipe_cache_service=recipe_cache_service,
            thread_service=thread_service,
            message_service=message_service,
            recipe_service=recipe_service,
        )
    
    def _stop(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stream_processor.stop(signum, frame)

    
    async def run(self) -> None:
        logger.info("Starting chat session data stream processor worker...")
        
        await self.stream_processor.run()
        
        logger.info("Chat session data stream processor worker stopped.")


async def main():
    """Main entry point for the chat session data stream processor worker."""
    worker = ChatSessionDataStreamProcessorWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main()) 