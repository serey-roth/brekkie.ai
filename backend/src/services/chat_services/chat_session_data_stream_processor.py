import json
import signal
from datetime import datetime, timezone
import redis
from typing import Any, List, Tuple, cast

from database.index import DBTransactionMaker

from services.redis.redis_client import RedisClient
from services.data_services.thread_cache_service import ThreadCacheService
from services.data_services.message_cache_service import MessageCacheService
from services.data_services.recipe_cache_service import RecipeCacheService
from services.data_services.thread_service import ThreadService
from services.data_services.message_service import MessageService
from services.data_services.recipe_service import RecipeService

from schemas.chat_session_data_stream import (
    ChatSessionDataStreamEntry, 
    ChatSessionStreamEntryType,
    SyncCachedThreadWithDbEntry,
    SyncCachedMessageWithDbEntry,
    SyncCachedRecipeWithDbEntry,
)
from schemas.messages import (
    CreateMessageParams,
    GetMessagesParams,
    UpdateMessageInputTokensParams,
    UpdateMessageOutputTokensParams,
    UpdateMessageParams,
    UpdateMessageTextContentParams,
    UpdateStrategy,
)
from schemas.recipes import CreateRecipeParams, UpdateRecipeParams, UserRecipe
from schemas.threads import CreateThreadParams, GetUserThreadsParams, UpdateThreadParams

from utils.logger import Logger

logger = Logger("chat_session_data_stream_processor")

MAX_RETRIES = 5


class RetryException(Exception):
    pass


class ChatSessionDataStreamProcessor:
    def __init__(
        self,
        stream: str,
        group: str,
        consumer_name: str,
        redis_client: RedisClient,
        db_transaction_maker: DBTransactionMaker,
        thread_cache_service: ThreadCacheService,   
        message_cache_service: MessageCacheService,
        recipe_cache_service: RecipeCacheService,
        thread_service: ThreadService,
        message_service: MessageService,
        recipe_service: RecipeService,
        block_time: int = 5000,
        stop_when_stream_empty: bool = False,
    ):
        self.stream = stream
        self.group = group
        self.consumer_name = consumer_name
        self.block_time = block_time
        self.stop_when_stream_empty = stop_when_stream_empty
        self.should_run = True
        
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

        self.redis_client = redis_client
        self.db_transaction_maker = db_transaction_maker

        self.thread_cache_service = thread_cache_service
        self.message_cache_service = message_cache_service
        self.recipe_cache_service = recipe_cache_service
        self.thread_service = thread_service
        self.message_service = message_service
        self.recipe_service = recipe_service

    def stop(self, signum: int, frame: Any) -> None:
        logger.info(f"Received signal {signum}. Stopping stream processor.")
        self.should_run = False

    async def run(self) -> None:
        await self._ensure_group_exists()

        logger.info(f"Running stream processor for group {self.group}")

        while self.should_run:
            try:
                raw_entries = await self.redis_client.xreadgroup(
                    self.group, self.consumer_name, {self.stream: ">"}, count=1, block=self.block_time
                )
            except redis.RedisError as e:
                logger.error(f"Error reading stream: {e}")
                continue

            if self.stop_when_stream_empty and len(raw_entries) == 0:
                logger.info("Stream is empty, stopping stream processor")
                break

            entries = cast(List[Tuple[str, List[Tuple[str, List[Tuple[str, str]]]]]], raw_entries)

            for _, stream_entries in entries:
                for entry_id, raw_data in stream_entries:
                    if not self.should_run:
                        logger.info("Stopping stream processor")
                        break

                    try:
                        logger.info(f"Processing entry {entry_id}: {raw_data}")
                        await self._process_entry(entry_id, raw_data)
                    except RetryException as e:
                        logger.warning(f"Retrying entry {entry_id} due to {e}")
                        continue

    async def _ensure_group_exists(self) -> None:
        try:
            await self.redis_client.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except redis.RedisError as e:
            if e.args[0] == "BUSYGROUP Consumer Group name already exists":
                logger.info(f"Group {self.group} already exists")
            else:
                raise e

    async def _process_entry(self, msg_id: str, raw_data: List[Tuple[str, str]]) -> None:
        logger.info(f"Processing entry {msg_id} with raw_data: {raw_data}")
        
        data: dict[str | bytes, str | bytes] = {}
        if isinstance(raw_data, dict):
            data = raw_data
        else:
            data = {k: v for k, v in raw_data}
        
        try:
            raw_type: str | bytes | None = data.get("type") or data.get(b"type")
            if not raw_type:
                logger.warning(f"Missing type in stream entry: {data}")
                await self.redis_client.xack(self.stream, self.group, msg_id)
                return
            
            raw_payload: str | bytes | None = data.get("payload") or data.get(b"payload")
            if not raw_payload:
                logger.warning(f"Missing payload in stream entry: {data}")
                await self.redis_client.xack(self.stream, self.group, msg_id)
                return
            
            # Decode bytes to string if needed
            if isinstance(raw_type, bytes):
                raw_type = raw_type.decode()
            if isinstance(raw_payload, bytes):
                raw_payload = raw_payload.decode()
            
            payload_data = json.loads(raw_payload)
            
            entry = ChatSessionDataStreamEntry.model_validate({
                "type": ChatSessionStreamEntryType(raw_type),
                "payload": payload_data
            })
            
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Invalid stream entry data: {data}, error: {e}")
            await self.redis_client.xack(self.stream, self.group, msg_id)
            return
        
        except Exception as e:
            logger.warning(f"Error processing stream entry: {data}, error: {e}")
            await self.redis_client.xack(self.stream, self.group, msg_id)
            return

        try:
            await self._call_process_handler(entry, msg_id)

            # ✅ Only ack here if we've successfully processed the entry
            await self.redis_client.xack(self.stream, self.group, msg_id)

        except Exception as e:
            pending_info = await self.redis_client.xpending(self.stream, self.group)
            retry_entry = next(
                (entry for entry in pending_info["pending"] if entry["message_id"] == msg_id), None
            )

            if retry_entry:
                delivery_count = retry_entry["delivery_count"]
                if delivery_count >= MAX_RETRIES:
                    logger.error(
                        f"❌ Max retries exceeded for message {msg_id}. Dropping. Error: {e}"
                    )
                    await self.redis_client.xack(self.stream, self.group, msg_id)
                else:
                    logger.warning(f"⚠️ Retry {delivery_count} for message {msg_id} failed: {e}")
            else:
                logger.warning(
                    f"🧐 Could not find retry info for message {msg_id}. Not acking to allow retry. Error: {e}"
                )
                
    async def _call_process_handler(self, entry: ChatSessionDataStreamEntry, msg_id: str) -> None:
        if entry.type == ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB and isinstance(entry.payload, SyncCachedThreadWithDbEntry):
            await self.sync_cached_thread_with_db(entry.payload)
        elif entry.type == ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB and isinstance(entry.payload, SyncCachedMessageWithDbEntry):
            await self.sync_cached_message_with_db(entry.payload)
        elif entry.type == ChatSessionStreamEntryType.SYNC_CACHED_RECIPE_WITH_DB and isinstance(entry.payload, SyncCachedRecipeWithDbEntry):
            await self.sync_cached_recipe_with_db(entry.payload)
        else:
            # This should never happen but in case it does, we'll ack the message
            logger.warning(f"Unknown entry type: {entry.type}")
            return

    async def sync_cached_thread_with_db(self, payload: SyncCachedThreadWithDbEntry) -> None:
        user_id = payload.user_id
        thread_id = payload.thread_id
        
        cached_thread = await self.thread_cache_service.get_thread(user_id, thread_id)
        if cached_thread is None:
            logger.info(f"Thread {thread_id} does not exist in cache")
            return
        
        if cached_thread.is_empty:
            logger.info(f"Thread {thread_id} is empty, skipping sync")
            return

        async with self.db_transaction_maker() as db:
            existing_thread = await self.thread_service.get_thread(db, thread_id)
            if existing_thread:
                if cached_thread.updated_at <= existing_thread.updated_at:
                    logger.info(
                        f"Thread {thread_id} already exists in database and does not need to be updated"
                    )
                    return
                else:
                    logger.info(
                        f"Thread {thread_id} already exists in database and needs to be updated"
                    )
                    await self.thread_service.update_thread(
                        db,
                        UpdateThreadParams(
                            id=thread_id,
                            updated_at=datetime.fromisoformat(cached_thread.updated_at).replace(
                                tzinfo=timezone.utc
                            ),
                            resumed_at=datetime.fromisoformat(cached_thread.resumed_at).replace(
                                tzinfo=timezone.utc
                            )
                            if cached_thread.resumed_at
                            else None,
                            is_empty=cached_thread.is_empty,
                            title=cached_thread.title,
                            summary=cached_thread.summary,
                            error_message=cached_thread.error_message,
                        ),
                    )
            else:
                logger.info(
                    f"Thread {thread_id} does not exist in database and needs to be created"
                )
                await self.thread_service.create_thread(
                    db,
                    CreateThreadParams(
                        user_id=user_id,
                        id=thread_id,
                        created_at=datetime.fromisoformat(cached_thread.created_at).replace(
                            tzinfo=timezone.utc
                        ),
                        updated_at=datetime.fromisoformat(cached_thread.updated_at).replace(
                            tzinfo=timezone.utc
                        ),
                        resumed_at=datetime.fromisoformat(cached_thread.resumed_at).replace(
                            tzinfo=timezone.utc
                        )
                        if cached_thread.resumed_at
                        else None,
                        is_empty=cached_thread.is_empty,
                        title=cached_thread.title,
                        summary=cached_thread.summary,
                        error_message=cached_thread.error_message,
                    ),
                )

    async def sync_cached_message_with_db(self, payload: SyncCachedMessageWithDbEntry) -> None:
        user_id = payload.user_id
        thread_id = payload.thread_id
        message_id = payload.message_id

        cached_message = await self.message_cache_service.get_message(
            user_id, thread_id, message_id
        )
        if cached_message is None:
            logger.info(f"Message {message_id} does not exist in cache")
            return

        async with self.db_transaction_maker() as db:
            existing_thread = await self.thread_service.get_thread(db, thread_id)
            if existing_thread is None:
                logger.warning(f"Thread {thread_id} does not exist in database")
                raise RetryException(f"Thread {thread_id} does not exist in database")

            if cached_message.parent_id is not None:
                parent_message = await self.message_service.get_message(
                    db, cached_message.parent_id
                )
                if parent_message is None:
                    logger.warning(
                        f"Parent message {cached_message.parent_id} does not exist in database"
                    )
                    raise RetryException(
                        f"Parent message {cached_message.parent_id} does not exist in database"
                    )
                    
            if cached_message.recipe_id is not None:
                recipe = await self.recipe_service.get_recipe(db, cached_message.recipe_id)
                if recipe is None:
                    logger.warning(f"Recipe {cached_message.recipe_id} does not exist in database")
                    raise RetryException(f"Recipe {cached_message.recipe_id} does not exist in database")

            existing_message = await self.message_service.get_message(db, message_id)
            if existing_message:
                if cached_message.updated_at <= existing_message.updated_at:
                    logger.info(
                        f"Message {message_id} already exists in database and does not need to be updated"
                    )
                    return
                else:
                    logger.info(
                        f"Message {message_id} already exists in database and needs to be updated"
                    )
                    await self.message_service.update_message(
                        db,
                        UpdateMessageParams(
                            id=message_id,
                            updated_at=datetime.fromisoformat(cached_message.updated_at).replace(
                                tzinfo=timezone.utc
                            ),
                            model_name=cached_message.model_name,
                            tool_name=cached_message.tool_name,
                            tool_input=cached_message.tool_input,
                            tool_output=cached_message.tool_output,
                            recipe_id=cached_message.recipe_id,
                            is_recipe_generation_started=cached_message.is_recipe_generation_started,
                            is_recipe_generation_completed=cached_message.is_recipe_generation_completed,
                            ip_address=cached_message.ip_address,
                            safety_guard_result=cached_message.safety_guard_result,
                            text_content_update=UpdateMessageTextContentParams(
                                text_content=cached_message.text_content,
                                strategy=UpdateStrategy.REPLACE,
                            )
                            if cached_message.text_content is not None
                            else None,
                            input_tokens_update=UpdateMessageInputTokensParams(
                                input_tokens=cached_message.input_tokens,
                                strategy=UpdateStrategy.REPLACE,
                            )
                            if cached_message.input_tokens is not None
                            else None,
                            output_tokens_update=UpdateMessageOutputTokensParams(
                                output_tokens=cached_message.output_tokens,
                                strategy=UpdateStrategy.REPLACE,
                            )
                            if cached_message.output_tokens is not None
                            else None,
                        ),
                    )
            else:
                logger.info(
                    f"Message {message_id} does not exist in database and needs to be created"
                )
                await self.message_service.create_message(
                    db,
                    CreateMessageParams(
                        id=message_id,
                        user_id=user_id,
                        thread_id=thread_id,
                        role=cached_message.role,
                        content_type=cached_message.content_type,
                        parent_id=cached_message.parent_id,
                        created_at=datetime.fromisoformat(cached_message.created_at).replace(
                            tzinfo=timezone.utc
                        ),
                        updated_at=datetime.fromisoformat(cached_message.updated_at).replace(
                            tzinfo=timezone.utc
                        ),
                        model_name=cached_message.model_name,
                        tool_name=cached_message.tool_name,
                        tool_input=cached_message.tool_input,
                        tool_output=cached_message.tool_output,
                        recipe_id=cached_message.recipe_id,
                        is_recipe_generation_started=cached_message.is_recipe_generation_started,
                        is_recipe_generation_completed=cached_message.is_recipe_generation_completed,
                        ip_address=cached_message.ip_address,
                        safety_guard_result=cached_message.safety_guard_result,
                        text_content=cached_message.text_content,
                        input_tokens=cached_message.input_tokens,
                        output_tokens=cached_message.output_tokens,
                    ),
                )

    async def sync_cached_recipe_with_db(self, payload: SyncCachedRecipeWithDbEntry) -> None:
        user_id = payload.user_id
        thread_id = payload.thread_id
        recipe_id = payload.recipe_id

        cached_recipe = await self.recipe_cache_service.get_recipe(user_id, thread_id, recipe_id)
        if cached_recipe is None:
            logger.info(f"Recipe {recipe_id} does not exist in cache")
            return

        async with self.db_transaction_maker() as db:
            thread = await self.thread_service.get_thread(db, thread_id)
            if thread is None:
                logger.warning(f"Thread {thread_id} does not exist in database")
                raise RetryException(f"Thread {thread_id} does not exist in database")

            existing_recipe = await self.recipe_service.get_recipe(db, recipe_id)
            if existing_recipe:
                if cached_recipe.updated_at <= existing_recipe.updated_at:
                    logger.info(
                        f"Recipe {recipe_id} already exists in database and does not need to be updated"
                    )
                    return
                else:
                    logger.info(
                        f"Recipe {recipe_id} already exists in database and needs to be updated"
                    )
                    await self.recipe_service.update_recipe(
                        db,
                        UpdateRecipeParams(
                            id=recipe_id,
                            updated_at=datetime.fromisoformat(cached_recipe.updated_at).replace(
                                tzinfo=timezone.utc
                            ),
                            ingredients=cached_recipe.ingredients,
                            instructions=cached_recipe.instructions,
                            categories=cached_recipe.categories,
                            **cached_recipe.model_dump(
                                exclude={
                                    "id",
                                    "user_id",
                                    "thread_id",
                                    "created_at",
                                    "updated_at",
                                    "ingredients",
                                    "instructions",
                                    "categories",
                                }
                            ),
                        ),
                    )
            else:
                logger.info(
                    f"Recipe {recipe_id} does not exist in database and needs to be created"
                )
                await self.recipe_service.create_recipe(
                    db,
                    CreateRecipeParams(
                        id=recipe_id,
                        user_id=user_id,
                        thread_id=thread_id,
                        created_at=datetime.fromisoformat(cached_recipe.created_at).replace(
                            tzinfo=timezone.utc
                        ),
                        updated_at=datetime.fromisoformat(cached_recipe.updated_at).replace(
                            tzinfo=timezone.utc
                        ),
                        ingredients=cached_recipe.ingredients,
                        instructions=cached_recipe.instructions,
                        categories=cached_recipe.categories,
                        **cached_recipe.model_dump(
                            exclude={
                                "id",
                                "user_id",
                                "thread_id",
                                "created_at",
                                "updated_at",
                                "ingredients",
                                "instructions",
                                "categories",
                            }
                        ),
                    ),
                )
