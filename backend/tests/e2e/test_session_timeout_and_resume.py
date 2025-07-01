import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock
import time

from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketState

from services.service_container import ServiceContainer

from schemas.messages import GetMessagesParams
from schemas.users import CreateUserParams


class TestSessionTimeoutAndResume:
    """Test cases for session timeout and thread resumption functionality."""
    
    def test_session_resume_flow(self, test_client: TestClient, service_container: ServiceContainer):
        """Test the complete flow: start thread -> disconnect -> resume thread."""
        print("\n🔄 Testing session resume flow...")
        
        # Step 1: Create user access and start a new thread
        user_access_data = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        print(f"👤 Created user access: {user_access_data.user_id}")
        
        # Start a new thread
        print("🧵 Starting new thread...")
        
        # Create WebSocket connection for new thread
        with test_client.websocket_connect(f"/ws/chat?access_token={user_access_data.access_token}") as websocket:
            # Send initial message to start the thread
            websocket.send_json({
                "id": "1",
                "content": "Hi! How are you?"
            })
            
            # Collect events until text_message_completed
            events = []
            max_events = 15
            final_response_completed = False
            
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track when we get the final text_message_completed
                    if event["event"] == "text_message_completed":
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            # Verify we got the expected events
            event_types = [e["event"] for e in events]
            print(f"📋 Event types: {event_types}")
            assert "thread_started" in event_types
            assert "text_message_completed" in event_types
            
            thread_started = next(e for e in events if e["event"] == "thread_started")
            thread_id = thread_started["data"]["thread"]["id"]
            print(f"🧵 Thread started: {thread_id}")
            print("🤖 AI response received")
            
            # Verify thread exists in cache
            cached_threads = asyncio.get_event_loop().run_until_complete(
                service_container.thread_cache_service.get_threads(user_access_data.user_id)
            )
            assert len(cached_threads) == 1
            assert cached_threads[0].id == thread_id
            print("✅ Thread verified in cache")
            
            # Send a second message
            websocket.send_json({
                "id": "2",
                "content": "This is a second message before disconnecting."
            })
            
            # Collect events until text_message_completed
            events = []
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track when we get the final text_message_completed
                    if event["event"] == "text_message_completed":
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            event_types = [e["event"] for e in events]
            assert "text_message_completed" in event_types
            print("🤖 Second AI response received")
            
            # Close the WebSocket connection (simulating disconnection)
            websocket.close()
            print("🔌 WebSocket disconnected")
        
        # Step 2: Resume the thread
        print("🔄 Resuming the disconnected thread...")
        
        # Create a new WebSocket connection to resume the thread
        with test_client.websocket_connect(f"/ws/chat/{thread_id}?access_token={user_access_data.access_token}") as websocket:
            # Wait for thread_resumed event
            event = websocket.receive_json()
            assert event["event"] == "thread_resumed"
            
            resumed_thread = event["data"]["thread"]
            assert resumed_thread["id"] == thread_id
            print(f"🧵 Thread resumed: {resumed_thread['id']}")
            
            # Verify thread data is loaded correctly
            messages = event["data"]["paginated_messages"]["messages"]
            assert len(messages) == 4  # 2 user messages + 2 AI responses
            print(f"💬 Loaded {len(messages)} messages from previous session")
            
            # Verify the thread is still accessible
            cached_threads = asyncio.get_event_loop().run_until_complete(
                service_container.thread_cache_service.get_threads(user_access_data.user_id)
            )
            assert len(cached_threads) == 1
            assert cached_threads[0].id == thread_id
            print("✅ Thread still accessible after resumption")
            
            # Step 3: Send a new message to verify the session is working
            print("💬 Sending new message to resumed session...")
            websocket.send_json({
                "id": "3",
                "content": "This is a follow-up message after resuming the session."
            })
            
            # Collect events until text_message_completed
            events = []
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track when we get the final text_message_completed
                    if event["event"] == "text_message_completed":
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            event_types = [e["event"] for e in events]
            assert "text_message_completed" in event_types
            print("🤖 AI response received in resumed session")
            
            # Verify new message was added
            cached_messages = asyncio.get_event_loop().run_until_complete(
                service_container.message_cache_service.get_messages_by_user_id(user_access_data.user_id)
            )
            assert len(cached_messages) == 6  # 3 user messages + 3 AI responses
            print(f"💬 Total messages after resumption: {len(cached_messages)}")
        
        print("✅ Session resume flow completed successfully!")

    def test_session_resume_with_authenticated_user(self, test_client: TestClient, service_container: ServiceContainer):
        """Test session resume with an authenticated user."""
        print("\n🔐 Testing session resume with authenticated user...")
        
        # Create authenticated user
        user_access_data = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        
        # Create user in database
        async def create_user():
            async with service_container.db_transaction_maker() as db:
                user = await service_container.user_service.create_user(
                    db,
                    CreateUserParams(
                        id="test-user-resume",
                        email="resume@example.com",
                        name="Resume Test User",
                        password="password123",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                )
                
                # Promote to authenticated
                authenticated_access = await service_container.user_access_cache_service.promote_to_authenticated(
                    access_token=user_access_data.access_token,
                    user_id=user.id,
                    email=user.email,
                    name=user.name
                )
                return authenticated_access
        
        authenticated_access = asyncio.get_event_loop().run_until_complete(create_user())
        print(f"👤 Created authenticated user: {authenticated_access.user_id}")
        
        # Start thread
        print("🧵 Starting thread for authenticated user...")
        
        with test_client.websocket_connect(f"/ws/chat?access_token={authenticated_access.access_token}") as websocket:
            websocket.send_json({
                "id": "1",
                "content": "Hello from authenticated user!"
            })
            
            # Collect events until text_message_completed
            events = []
            max_events = 15
            final_response_completed = False
            
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track when we get the final text_message_completed
                    if event["event"] == "text_message_completed":
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            # Verify we got the expected events
            event_types = [e["event"] for e in events]
            print(f"📋 Event types: {event_types}")
            assert "thread_started" in event_types
            assert "text_message_completed" in event_types
            
            thread_started = next(e for e in events if e["event"] == "thread_started")
            thread_id = thread_started["data"]["thread"]["id"]
            print(f"🧵 Thread created: {thread_id}")
            print("🤖 AI response received")
            
            # Send a second message before disconnecting
            websocket.send_json({
                "id": "2",
                "content": "This is a second message before disconnecting."
            })
            
            # Collect events until text_message_completed
            events = []
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track when we get the final text_message_completed
                    if event["event"] == "text_message_completed":
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            event_types = [e["event"] for e in events]
            assert "text_message_completed" in event_types
            print("🤖 Second AI response received")
            
            # Close the connection
            websocket.close()
            print("🔌 WebSocket disconnected")
        
        # Resume thread
        print("🔄 Resuming authenticated user thread...")
        
        with test_client.websocket_connect(f"/ws/chat/{thread_id}?access_token={authenticated_access.access_token}") as websocket:
            event = websocket.receive_json()
            assert event["event"] == "thread_resumed"
            
            # Verify thread data is loaded
            resumed_thread = event["data"]["thread"]
            assert resumed_thread["id"] == thread_id
            print(f"🧵 Thread resumed: {resumed_thread['id']}")
            
            # Verify thread data is loaded correctly
            messages = event["data"]["paginated_messages"]["messages"]
            assert len(messages) == 4  # 2 user messages + 2 AI responses
            print(f"💬 Loaded {len(messages)} messages from previous session")
            
            # Check that data is in database (not cache) for authenticated user
            async def check_database():
                async with service_container.db_transaction_maker() as db:
                    db_thread = await service_container.thread_service.get_thread(db, thread_id)
                    assert db_thread is not None
                    assert db_thread.user_id == authenticated_access.user_id
                    
                    db_messages = await service_container.message_service.get_paginated_messages(
                        db, GetMessagesParams(user_id=authenticated_access.user_id, thread_id=thread_id)
                    )
                    assert len(db_messages.messages) == 4  # 2 user messages + 2 AI responses
            
            asyncio.get_event_loop().run_until_complete(check_database())
            print("✅ Authenticated user thread resumed successfully")
            
            # Send follow-up message
            print("💬 Sending new message to resumed session...")
            websocket.send_json({
                "id": "3",
                "content": "This is a follow-up message after resuming the session."
            })
            
            # Collect events until text_message_completed
            events = []
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track when we get the final text_message_completed
                    if event["event"] == "text_message_completed":
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            event_types = [e["event"] for e in events]
            assert "text_message_completed" in event_types
            print("🤖 AI response received in resumed authenticated session")
            
            # Verify new message was added
            async def check_final_database():
                async with service_container.db_transaction_maker() as db:
                    final_messages = await service_container.message_service.get_paginated_messages(
                        db, GetMessagesParams(user_id=authenticated_access.user_id, thread_id=thread_id)
                    )
                    assert len(final_messages.messages) == 6  # 3 user messages + 3 AI responses
                    print(f"💬 Total messages after resumption: {len(final_messages.messages)}")
            
            asyncio.get_event_loop().run_until_complete(check_final_database())
        
        print("✅ Authenticated user session resume completed!")

    def test_session_resume_with_recipe_generation(self, test_client: TestClient, service_container: ServiceContainer):
        """Test session resume with recipe generation."""
        print("\n🍳 Testing session resume with recipe generation...")
        
        user_access_data = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        access_token = user_access_data.access_token
        print(f"🔑 Access token: {access_token[:20]}...")

        with test_client.websocket_connect(f"/ws/chat?access_token={access_token}") as websocket:
            # Send recipe generation request
            websocket.send_json({
                "id": "1",
                "content": "Use create_recipe tool to create a recipe for chocolate chip cookies"
            })
            
            # Collect events until recipe generation completes
            events = []
            recipe_field_events = []
            recipe_completed = False
            
            for _ in range(50):  # Try to receive up to 50 events (recipe generation takes more events)
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track recipe field events
                    if event["event"] == "recipe_field_detected":
                        recipe_field_events.append(event)
                        print(f"🍽️ Recipe field detected: {len(recipe_field_events)} total")
                    
                    # Track when recipe generation is completed
                    if event["event"] == "recipe_generation_completed":
                        recipe_completed = True
                        print(f"📥 Recipe generation completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            thread_started = next(e for e in events if e["event"] == "thread_started")
            thread_id = thread_started["data"]["thread"]["id"]
            
            print(f"🍽️ Received {len(recipe_field_events)} recipe fields")
            print(f"🍳 Recipe completed: {recipe_completed}")
            
            # Close the connection after recipe generation completes
            websocket.close()
            print("🔌 WebSocket disconnected after recipe generation completed")
        
        # Resume thread
        print("🔄 Resuming thread with partial recipe...")
        
        with test_client.websocket_connect(f"/ws/chat/{thread_id}?access_token={access_token}") as websocket:
            event = websocket.receive_json()
            assert event["event"] == "thread_resumed"
            
            resumed_thread = event["data"]["thread"]
            assert resumed_thread["id"] == thread_id
            
            # Verify partial recipe data is preserved
            messages = event["data"]["paginated_messages"]["messages"]
            recipes = event["data"]["recipes"]
            
            print(f"💬 Messages preserved: {len(messages)}")
            print(f"🍳 Recipes preserved: {len(recipes)}")
            
            # The recipe generation should be incomplete since it was interrupted
            # We can verify that the thread state is preserved
            cached_threads = asyncio.get_event_loop().run_until_complete(
                service_container.thread_cache_service.get_threads(user_access_data.user_id)
            )
            assert len(cached_threads) == 1
            assert cached_threads[0].id == thread_id
            
            print("✅ Thread state preserved after disconnection during recipe generation")
            
            # Send a message to continue the conversation
            websocket.send_json({
                "id": "2",
                "content": "Can you continue with the recipe?"
            })
            
            # Collect events until text_message_completed
            events = []
            max_events = 15
            final_response_completed = False
            
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track when we get the final text_message_completed
                    if event["event"] == "text_message_completed":
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            event_types = [e["event"] for e in events]
            assert "text_message_completed" in event_types
            print("🤖 AI response received in resumed session")
        
        print("✅ Recipe generation resume completed!")

    def test_session_resume_error_handling(self, test_client: TestClient, service_container: ServiceContainer):
        """Test error handling during session resume scenarios."""
        print("\n⚠️ Testing session resume error handling...")
        
        user_access_data = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        print(f"👤 Created user access: {user_access_data.user_id}")
        
        # Test 1: Try to resume a non-existent thread
        print("🔍 Testing resume of non-existent thread...")
        
        fake_thread_id = "non-existent-thread-id"
        with test_client.websocket_connect(f"/ws/chat/{fake_thread_id}?access_token={user_access_data.access_token}") as websocket:
            response = websocket.receive_json()
            assert response["event"] == "chat_session_error"
            assert response["data"]["type"] == "thread_not_found"
            print("✅ Correctly handled non-existent thread resume")
        
        # Test 2: Try to resume with invalid access token
        print("🔍 Testing resume with invalid access token...")
        
        # First create a real thread
        with test_client.websocket_connect(f"/ws/chat?access_token={user_access_data.access_token}") as websocket:
            websocket.send_json({
                "id": "1",
                "content": "Hello!"
            })
            
            # Collect events until text_message_completed
            events = []
            max_events = 15
            final_response_completed = False
            
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track when we get the final text_message_completed
                    if event["event"] == "text_message_completed":
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            thread_started = next(e for e in events if e["event"] == "thread_started")
            thread_id = thread_started["data"]["thread"]["id"]
        
        # Now try to resume with invalid token
        invalid_token = "invalid-access-token"
        with test_client.websocket_connect(f"/ws/chat/{thread_id}?access_token={invalid_token}") as websocket:
            response = websocket.receive_json()
            assert response["event"] == "chat_session_error"
            assert response["data"]["type"] == "access_token_not_found"
            print("✅ Correctly handled invalid access token")
        
        # Test 3: Try to resume with expired token
        print("🔍 Testing resume with expired token...")
        
        # Create an expired token scenario
        expired_access_data = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        
        # Manually expire the token by setting a very short TTL
        with patch.object(service_container.user_access_cache_service, 'ttl', 1):
            # Wait for token to expire
            time.sleep(2)
            
            with test_client.websocket_connect(f"/ws/chat/{thread_id}?access_token={expired_access_data.access_token}") as websocket:
                response = websocket.receive_json()
                assert response["event"] == "chat_session_error"
                print("✅ Correctly handled expired access token")
        
        print("✅ Session resume error handling tests completed!")

    def test_session_resume_persistence_verification(self, test_client: TestClient, service_container: ServiceContainer):
        """Test that data persists correctly across session disconnections."""
        print("\n💾 Testing data persistence across session disconnections...")
        
        user_access_data = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        print(f"👤 Created user access: {user_access_data.user_id}")
        
        # Start thread and send multiple messages
        print("🧵 Starting thread with multiple messages...")
        
        with test_client.websocket_connect(f"/ws/chat?access_token={user_access_data.access_token}") as websocket:
            # Send first message
            websocket.send_json({
                "id": "1",
                "content": "First message before disconnection"
            })
            
            # Collect events until text_message_completed
            events = []
            max_events = 15
            final_response_completed = False
            
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track when we get the final text_message_completed
                    if event["event"] == "text_message_completed":
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            thread_started = next(e for e in events if e["event"] == "thread_started")
            thread_id = thread_started["data"]["thread"]["id"]
            
            # Send second message
            websocket.send_json({
                "id": "2",
                "content": "Second message before disconnection"
            })
            
            # Collect events until text_message_completed
            events = []
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track when we get the final text_message_completed
                    if event["event"] == "text_message_completed":
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            print(f"💬 Sent 2 messages, thread ID: {thread_id}")
            
            # Close the connection
            websocket.close()
            print("🔌 WebSocket disconnected")
        
        # Verify data persistence
        print("🔍 Verifying data persistence...")
        
        # Check cache for anonymous user
        cached_threads = asyncio.get_event_loop().run_until_complete(
            service_container.thread_cache_service.get_threads(user_access_data.user_id)
        )
        assert len(cached_threads) == 1
        assert cached_threads[0].id == thread_id
        
        cached_messages = asyncio.get_event_loop().run_until_complete(
            service_container.message_cache_service.get_messages_by_user_id(user_access_data.user_id)
        )
        assert len(cached_messages) == 4  # 2 user messages + 2 AI responses
        print(f"💬 Cached messages: {len(cached_messages)}")
        
        # Resume thread and verify all data is intact
        print("🔄 Resuming thread to verify data integrity...")
        
        with test_client.websocket_connect(f"/ws/chat/{thread_id}?access_token={user_access_data.access_token}") as websocket:
            event = websocket.receive_json()
            assert event["event"] == "thread_resumed"
            
            resumed_data = event["data"]
            resumed_messages = resumed_data["paginated_messages"]["messages"]
            
            assert len(resumed_messages) == 4  # All messages should be preserved
            print(f"💬 Resumed messages: {len(resumed_messages)}")
            
            # Verify message content is preserved
            user_messages = [msg["text_content"] for msg in resumed_messages if msg["role"] == "user"]
            assert len(user_messages) == 2
            assert "First message before disconnection" in user_messages
            assert "Second message before disconnection" in user_messages
            
            print("✅ Message content preserved correctly")
            
            # Send a new message to verify the session continues working
            websocket.send_json({
                "id": "3",
                "content": "Third message after resumption"
            })
            
            # Collect events until text_message_completed
            events = []
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track when we get the final text_message_completed
                    if event["event"] == "text_message_completed":
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            event_types = [e["event"] for e in events]
            assert "text_message_completed" in event_types
            print("🤖 AI response received in resumed session")
        
        # Final verification
        final_messages = asyncio.get_event_loop().run_until_complete(
            service_container.message_cache_service.get_messages_by_user_id(user_access_data.user_id)
        )
        assert len(final_messages) == 6  # 3 user messages + 3 AI responses
        print(f"💬 Final message count: {len(final_messages)}")
        
        print("✅ Data persistence verification completed!")

    def test_session_timeout_mechanism(self, test_client: TestClient, service_container: ServiceContainer):
        """Test the session timeout mechanism with a shorter TTL for testing."""
        print("\n⏰ Testing session timeout mechanism...")
        
        user_access_data = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        print(f"👤 Created user access: {user_access_data.user_id}")
        
        # Override the session TTL to a shorter duration for testing
        with patch.object(service_container.chat_session_orchestrator, 'session_ttl', 10):  # 10 seconds timeout
            print("🧵 Starting thread with 10-second timeout...")
            
            with test_client.websocket_connect(f"/ws/chat?access_token={user_access_data.access_token}") as websocket:
                websocket.send_json({
                    "id": "1",
                    "content": "Hello! This is a test for session timeout."
                })
                
                # Collect events until text_message_completed
                events = []
                max_events = 15
                final_response_completed = False
                
                for _ in range(max_events):
                    try:
                        event = websocket.receive_json()
                        print(f"📥 Received event: {event['event']}")
                        events.append(event)
                        
                        # Track when we get the final text_message_completed
                        if event["event"] == "text_message_completed":
                            final_response_completed = True
                            print(f"📥 Final response completed")
                            # Wait a bit for any additional events like thread_title_updated
                            time.sleep(1.0)
                            break
                                
                    except Exception as e:
                        # No more events
                        print(f"📥 No more events: {e}")
                        break
                
                # Verify we got the expected events
                event_types = [e["event"] for e in events]
                print(f"📋 Event types: {event_types}")
                assert "thread_started" in event_types
                assert "text_message_completed" in event_types
                
                thread_started = next(e for e in events if e["event"] == "thread_started")
                thread_id = thread_started["data"]["thread"]["id"]
                print(f"🧵 Thread started: {thread_id}")
                print("🤖 AI response received")
                print("⏰ Waiting for session timeout (10 seconds)...")
                
                # Wait for the session to timeout naturally
                time.sleep(12)  # Wait slightly longer than the 10-second timeout
                print("⏰ Session timeout period completed")
                
                # The WebSocket should be closed by the timeout mechanism
                # We don't need to manually close it
                print("🔌 WebSocket should be closed by timeout mechanism")
        
        # Resume the thread
        print("🔄 Resuming thread after timeout...")
        
        with test_client.websocket_connect(f"/ws/chat/{thread_id}?access_token={user_access_data.access_token}") as websocket:
            event = websocket.receive_json()
            assert event["event"] == "thread_resumed"
            
            resumed_thread = event["data"]["thread"]
            assert resumed_thread["id"] == thread_id
            print(f"🧵 Thread resumed: {resumed_thread['id']}")
            
            # Verify data is preserved
            messages = event["data"]["paginated_messages"]["messages"]
            assert len(messages) == 2  # User message + AI response
            print(f"💬 Messages preserved: {len(messages)}")
            
            # Send a follow-up message
            websocket.send_json({
                "id": "2",
                "content": "Follow-up message after timeout."
            })
            
            # Collect events until text_message_completed
            events = []
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track when we get the final text_message_completed
                    if event["event"] == "text_message_completed":
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                            
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break
            
            event_types = [e["event"] for e in events]
            assert "text_message_completed" in event_types
            print("🤖 AI response received after timeout")
        
        print("✅ Session timeout mechanism test completed!") 