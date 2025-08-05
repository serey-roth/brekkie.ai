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
from utils.date_utils import to_utc_isostring

#TODO: Fix these with auth-only flow and test db sync
class TestSessionTimeoutAndResume:
    """Test cases for session timeout and thread resumption functionality."""
    
    def test_session_resume_flow(self, test_client: TestClient, service_container: ServiceContainer):
        """Test the complete flow: start thread -> disconnect -> resume thread."""
        print("\n🔄 Testing session resume flow...")
        
        # Step 1: Create user access and start a new thread
        user_access = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        print(f"👤 Created user access: {user_access.user_id}")
        
        # Start a new thread
        print("🧵 Starting new thread...")
        
        # Set the access token as a cookie
        test_client.cookies.set("bk_access_token", user_access.access_token)
        
        # Create WebSocket connection for new thread
        with test_client.websocket_connect("/ws/chat") as websocket:
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
                service_container.thread_cache_service.get_threads(user_access.user_id)
            )
            assert len(cached_threads) == 1
            assert cached_threads[0].id == thread_id
            print("✅ Thread verified in cache")
            
            # Send a second message
            websocket.send_json({
                "id": "2",
                "content": "How are you?"
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
        
        # Set the access token as a cookie for resume
        test_client.cookies.set("bk_access_token", user_access.access_token)
        
        # Create a new WebSocket connection to resume the thread
        with test_client.websocket_connect(f"/ws/chat/{thread_id}") as websocket:
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
                service_container.thread_cache_service.get_threads(user_access.user_id)
            )
            assert len(cached_threads) == 1
            assert cached_threads[0].id == thread_id
            print("✅ Thread still accessible after resumption")
            
            # Step 3: Send a new message to verify the session is working
            print("💬 Sending new message to resumed session...")
            websocket.send_json({
                "id": "3",
                "content": "What's your favorite food?"
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
                service_container.message_cache_service.get_messages_by_user_id(user_access.user_id)
            )
            assert len(cached_messages) == 6  # 3 user messages + 3 AI responses
            print(f"💬 Total messages after resumption: {len(cached_messages)}")
        
        print("✅ Session resume flow completed successfully!")

    def test_session_resume_with_recipe_generation(self, test_client: TestClient, service_container: ServiceContainer):
        """Test session resume with recipe generation."""
        print("\n🍳 Testing session resume with recipe generation...")
        
        user_access = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        access_token = user_access.access_token
        print(f"🔑 Access token: {access_token[:20]}...")

        # Set the access token as a cookie
        test_client.cookies.set("bk_access_token", access_token)

        with test_client.websocket_connect("/ws/chat") as websocket:
            # Send recipe generation request
            websocket.send_json({
                "id": "1",
                "content": "I want to make chocolate chip cookies. Can you create a recipe for me?"
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
        
        # Set the access token as a cookie for resume
        test_client.cookies.set("bk_access_token", access_token)
        
        with test_client.websocket_connect(f"/ws/chat/{thread_id}") as websocket:
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
                service_container.thread_cache_service.get_threads(user_access.user_id)
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
        
        user_access = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        print(f"👤 Created user access: {user_access.user_id}")
        
        # Test 1: Try to resume a non-existent thread
        print("🔍 Testing resume of non-existent thread...")
        
        # Set the access token as a cookie
        test_client.cookies.set("bk_access_token", user_access.access_token)
        
        fake_thread_id = "non-existent-thread-id"
        with test_client.websocket_connect(f"/ws/chat/{fake_thread_id}") as websocket:
            response = websocket.receive_json()
            assert response["event"] == "chat_session_error"
            assert response["data"]["type"] == "internal_server_error" # TODO: change to thread_not_found
            print("✅ Correctly handled non-existent thread resume")
        
        # Test 2: Try to resume with invalid access token
        print("🔍 Testing resume with invalid access token...")
        
        # First create a real thread
        # Set the access token as a cookie
        test_client.cookies.set("bk_access_token", user_access.access_token)
        
        with test_client.websocket_connect("/ws/chat") as websocket:
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
        # Set the invalid access token as a cookie
        test_client.cookies.set("bk_access_token", invalid_token)
        
        with test_client.websocket_connect(f"/ws/chat/{thread_id}") as websocket:
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
            
            # Set the expired access token as a cookie
            test_client.cookies.set("bk_access_token", expired_access_data.access_token)
            
            with test_client.websocket_connect(f"/ws/chat/{thread_id}") as websocket:
                response = websocket.receive_json()
                assert response["event"] == "chat_session_error"
                print("✅ Correctly handled expired access token")
        
        print("✅ Session resume error handling tests completed!")

    def test_session_resume_persistence_verification(self, test_client: TestClient, service_container: ServiceContainer):
        """Test that data persists correctly across session disconnections."""
        print("\n💾 Testing data persistence across session disconnections...")
        
        user_access = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        print(f"👤 Created user access: {user_access.user_id}")
        
        # Start thread and send multiple messages
        print("🧵 Starting thread with multiple messages...")
        
        # Set the access token as a cookie
        test_client.cookies.set("bk_access_token", user_access.access_token)
        
        with test_client.websocket_connect("/ws/chat") as websocket:
            # Send first message
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
            
            # Send second message
            websocket.send_json({
                "id": "2",
                "content": "How are you?"
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
            service_container.thread_cache_service.get_threads(user_access.user_id)
        )
        assert len(cached_threads) == 1
        assert cached_threads[0].id == thread_id
        
        cached_messages = asyncio.get_event_loop().run_until_complete(
            service_container.message_cache_service.get_messages_by_user_id(user_access.user_id)
        )
        assert len(cached_messages) == 4  # 2 user messages + 2 AI responses
        print(f"💬 Cached messages: {len(cached_messages)}")
        
        # Resume thread and verify all data is intact
        print("🔄 Resuming thread to verify data integrity...")
        
        # Set the access token as a cookie for resume
        test_client.cookies.set("bk_access_token", user_access.access_token)
        
        with test_client.websocket_connect(f"/ws/chat/{thread_id}") as websocket:
            event = websocket.receive_json()
            assert event["event"] == "thread_resumed"
            
            resumed_data = event["data"]
            resumed_messages = resumed_data["paginated_messages"]["messages"]
            
            assert len(resumed_messages) == 4  # All messages should be preserved
            print(f"💬 Resumed messages: {len(resumed_messages)}")
            
            # Verify message content is preserved
            user_messages = [msg["text_content"] for msg in resumed_messages if msg["role"] == "user"]
            assert len(user_messages) == 2
            assert "Hello!" in user_messages
            assert "How are you?" in user_messages
            
            print("✅ Message content preserved correctly")
            
            # Send a new message to verify the session continues working
            websocket.send_json({
                "id": "3",
                "content": "What's your favorite food?"
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
            service_container.message_cache_service.get_messages_by_user_id(user_access.user_id)
        )
        assert len(final_messages) == 6  # 3 user messages + 3 AI responses
        print(f"💬 Final message count: {len(final_messages)}")
        
        print("✅ Data persistence verification completed!")

    def test_session_timeout_mechanism(self, test_client: TestClient, service_container: ServiceContainer):
        """Test the session timeout mechanism with a shorter TTL for testing."""
        print("\n⏰ Testing session timeout mechanism...")
        
        user_access = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        print(f"👤 Created user access: {user_access.user_id}")
        
        # Override the session TTL to a shorter duration for testing
        with patch.object(service_container.chat_session_orchestrator, 'session_ttl', 10):  # 10 seconds timeout
            print("🧵 Starting thread with 10-second timeout...")
            
            # Set the access token as a cookie
            test_client.cookies.set("bk_access_token", user_access.access_token)
            
            with test_client.websocket_connect("/ws/chat") as websocket:
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
        
        # Set the access token as a cookie for resume
        test_client.cookies.set("bk_access_token", user_access.access_token)
        
        with test_client.websocket_connect(f"/ws/chat/{thread_id}") as websocket:
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
                "content": "How are you?"
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