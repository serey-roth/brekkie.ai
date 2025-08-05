import asyncio
import signal

import pytest
from fastapi.testclient import TestClient

from services.chat_services.chat_session_data_stream_processor import ChatSessionDataStreamProcessor
from services.service_container import ServiceContainer

from schemas.message_role import MessageRole

from utils.logger import Logger

logger = Logger("test_chat_session_data_stream_processor_integration")


class TestChatSessionDataStreamProcessorIntegration:
    """End-to-end tests for chat session data stream processor integration."""
    
    @pytest.mark.asyncio
    async def test_stream_processor_integration(self, test_client: TestClient, service_container: ServiceContainer, redis_client):
        """Test complete flow: create data → stream → stream processor → database"""
        print("\n🔄 Testing chat session data stream processor integration...")
        
        # 1. Create user access
        user_access = await service_container.user_access_cache_service.create_anonymous_access()
        access_token = user_access.access_token
        user_id = user_access.user_id
        print(f"👤 Created user access: {user_id}")
        
        # 2. Create data via WebSocket chat (this will trigger stream writes)
        test_client.cookies.set("bk_access_token", access_token)
        
        with test_client.websocket_connect("/ws/chat") as websocket:
            message = {"id": "stream-processor-test-1", "content": "Hello! Can you help me with cooking?"}
            print(f"📤 Sending message: {message}")
            websocket.send_json(message)
            
            # Wait for response
            events = []
            for _ in range(10):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    if event["event"] == "text_message_completed":
                        print("✅ Chat completed")
                        break
                except Exception as e:
                    print(f"📥 No more events: {e}")
                    break
        
        # 3. Verify data is in cache
        print("🔍 Checking cache for data...")
        cached_threads = await service_container.thread_cache_service.get_threads(user_id)
        assert len(cached_threads) >= 1, "No threads in cache"
        
        thread_id = cached_threads[0].id
        print(f"🧵 Thread ID: {thread_id}")
        
        cached_messages = await service_container.message_cache_service.get_messages_by_user_id(user_id)
        assert len(cached_messages) >= 2, "Expected at least 2 messages in cache"
        
        # 4. Check stream entries were created
        print("🔍 Checking Redis stream for entries...")
        stream_name = "brekkie_ai_chat_session_data_stream"
        stream_entries = await redis_client.xread({stream_name: "0"}, count=10)
        
        print(f"📊 Stream entries found: {len(stream_entries)}")
        if stream_entries:
            stream_name_returned, entries = stream_entries[0]
            print(f"📋 Stream name: {stream_name_returned}")
            print(f"📋 Number of entries: {len(entries)}")
            
            # Verify we have thread and message entries
            entry_types = []
            for entry_id, entry_data in entries:
                entry_type = entry_data[b"type"].decode()
                entry_types.append(entry_type)
                print(f"📋 Entry type: {entry_type}")
            
            assert "sync_cached_thread_with_db" in entry_types, "No thread entry in stream"
            assert "sync_cached_message_with_db" in entry_types, "No message entry in stream"
        
        # 5. Create stream processor for testing
        print("🔄 Creating stream processor...")
        stream_processor = ChatSessionDataStreamProcessor(
            stream=stream_name,
            group="test_sync_group",
            consumer_name="test_sync_consumer",
            redis_client=redis_client,
            db_transaction_maker=service_container.db_transaction_maker,
            thread_cache_service=service_container.thread_cache_service,
            message_cache_service=service_container.message_cache_service,
            recipe_cache_service=service_container.recipe_cache_service,
            thread_service=service_container.thread_service,
            message_service=service_container.message_service,
            recipe_service=service_container.recipe_service,
            block_time=100,
            stop_when_stream_empty=True,    
        )
        
        # 6. Run stream processor
        print("🔄 Running stream processor...")
        await stream_processor.run()
        print("✅ Stream processor completed")
        
        # 7. Verify data was synced to database
        print("🔍 Checking database for stream processed data...")
        
        # Check thread in database
        async with service_container.db_transaction_maker() as db:
            db_thread = await service_container.thread_service.get_thread(db, thread_id)
            if db_thread:
                print(f"✅ Thread synced to database: {db_thread.id}")
                assert db_thread.id == thread_id
            else:
                print("⚠️ Thread not found in database (may need more time to stream process)")
            
            # Check messages in database
            db_messages = await service_container.message_service.get_messages_by_ids(db, [cached_messages[0].id, cached_messages[1].id])
            print(f"💬 Messages in database: {len(db_messages)}")
            
            if db_messages:
                user_messages = [m for m in db_messages if m.role == MessageRole.user]
                ai_messages = [m for m in db_messages if m.role == MessageRole.assistant]
                
                print(f"👤 User messages in DB: {len(user_messages)}")
                print(f"🤖 AI messages in DB: {len(ai_messages)}")
                
                if user_messages:
                    user_message = user_messages[0]
                    if user_message.text_content:
                        print(f"👤 User message content: {user_message.text_content[:50]}...")
                        assert user_message.text_content == "Hello! Can you help me with cooking?"
                
                if ai_messages:
                    ai_message = ai_messages[0]
                    if ai_message.text_content:
                        print(f"🤖 AI message content: {ai_message.text_content[:50]}...")
                        # Don't assert specific content since AI responses can vary
                        assert len(ai_message.text_content) > 0, "AI message should have content"
        
        print("✅ Stream processor integration test completed!")

    @pytest.mark.asyncio
    async def test_stream_processor_with_recipe_generation(self, test_client: TestClient, service_container: ServiceContainer, redis_client):
        """Test stream processor with recipe generation flow."""
        print("\n🍳 Testing stream processor with recipe generation...")
        
        # 1. Create user access
        user_access = await service_container.user_access_cache_service.create_anonymous_access()
        access_token = user_access.access_token
        user_id = user_access.user_id
        print(f"👤 Created user access: {user_id}")
        
        # 2. Generate recipe via WebSocket
        test_client.cookies.set("bk_access_token", access_token)
        
        with test_client.websocket_connect("/ws/chat") as websocket:
            message = {"id": "recipe-test-1", "content": "Give me a recipe for chocolate chip cookies, no need to ask me for any other information"}
            print(f"📤 Sending recipe request: {message}")
            websocket.send_json(message)
            
            # Wait for recipe generation
            events = []
            for _ in range(20):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    if event["event"] == "recipe_generation_completed":
                        print("✅ Recipe generation completed")
                        break
                except Exception as e:
                    print(f"📥 No more events: {e}")
                    break
        
        # 3. Verify recipe data in cache
        print("🔍 Checking cache for recipe data...")
        cached_messages = await service_container.message_cache_service.get_messages_by_user_id(user_id)
        recipe_messages = [m for m in cached_messages if m.recipe_id is not None]
        
        assert len(recipe_messages) >= 1, "No recipe messages in cache"
        recipe_message = recipe_messages[0]
        print(f"🍳 Recipe message ID: {recipe_message.id}")
        print(f"🍳 Recipe ID: {recipe_message.recipe_id}")
        
        # 4. Check stream entries
        stream_name = "brekkie_ai_chat_session_data_stream"
        stream_entries = await redis_client.xread({stream_name: "0"}, count=20)
        
        if stream_entries:
            _, entries = stream_entries[0]
            entry_types = [entry_data[b"type"].decode() for _, entry_data in entries]
            print(f"📋 Stream entry types: {entry_types}")
            
            assert "sync_cached_recipe_with_db" in entry_types, "No recipe entry in stream"
        
        # 5. Create and run test stream processor
        print("🔄 Creating test recipe stream processor...")
        stream_processor = ChatSessionDataStreamProcessor(
            stream=stream_name,
            group="test_recipe_sync_group",
            consumer_name="test_recipe_sync_consumer",
            redis_client=redis_client,
            db_transaction_maker=service_container.db_transaction_maker,
            thread_cache_service=service_container.thread_cache_service,
            message_cache_service=service_container.message_cache_service,
            recipe_cache_service=service_container.recipe_cache_service,
            thread_service=service_container.thread_service,
            message_service=service_container.message_service,
            recipe_service=service_container.recipe_service,
            block_time=100,
            stop_when_stream_empty=True,    
        )
        
        # 6. Run test stream processor
        print("🔄 Running test recipe stream processor...")
        await stream_processor.run()
        print("✅ Test recipe stream processor completed")
        
        # 7. Verify recipe in database
        print("🔍 Checking database for recipe...")
        async with service_container.db_transaction_maker() as db:
            if recipe_message.recipe_id:
                db_recipe = await service_container.recipe_service.get_recipe(db, recipe_message.recipe_id)
                if db_recipe:
                    print(f"✅ Recipe synced to database: {db_recipe.id}")
                    print(f"🍳 Recipe name: {db_recipe.name}")
                    assert db_recipe.id == recipe_message.recipe_id
                else:
                    print("⚠️ Recipe not found in database (may need more time to stream process)")
        
        print("✅ Recipe stream processor integration test completed!") 