import asyncio
from datetime import datetime, timezone
import pytest
import time

from fastapi.testclient import TestClient   

from services.service_container import ServiceContainer

from schemas.threads import GetUserThreadsParams
from schemas.messages import GetMessagesParams
from schemas.message_role import MessageRole
from schemas.users import CreateUserParams



class TestRealChatFlow:
    """End-to-end tests for real chat flow with WebSocket and AI integration."""
    
    @pytest.mark.asyncio(loop_scope="session")
    async def test_ai_food_agent_integration(self, service_container: ServiceContainer):
        """Test AI service directly without WebSocket to verify AI integration."""
        print("\n🤖 Testing AI service directly...")
        
        # Debug: Check if we have real services
        print(f"🔍 AI Food Agent type: {type(service_container.ai_food_agent)}")
        
        # Create user access
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        print(f"👤 Created user access: {user_access_data.user_id}")
        
        # Test AI service directly
        try:
            # Create a simple message to test AI processing
            message_content = "Hello! Can you help me with cooking?"
            print(f"💬 Testing AI with message: {message_content}")
            
            # Collect events to verify AI is working
            events_received = []
            
            async def on_event(event):
                events_received.append(event)
                print(f"📥 Received event: {event.event}")
            
            # Test the AI service directly
            await service_container.ai_food_agent.stream_conversation(
                user_id=user_access_data.user_id,
                thread_id="test-thread",
                user_input=message_content,
                on_event=on_event
            )
            
            print(f"📊 Total events received: {len(events_received)}")
            
            # Verify we got some events
            assert len(events_received) > 0, "No events received from AI service"
            
            # Check for specific event types
            event_types = [event.event for event in events_received]
            print(f"📋 Event types received: {event_types}")
            
            # Should have at least a text message started and completed
            assert "text_message_started" in event_types, "No text message started event"
            assert "text_message_completed" in event_types, "No text message completed event"
            
            # Get the full response
            text_completed_events = [e for e in events_received if e.event == "text_message_completed"]
            if text_completed_events:
                full_response = text_completed_events[0].payload.full_message
                print(f"🤖 AI Response: {full_response[:100]}...")
                assert len(full_response) > 0, "AI response is empty"
            
            print("✅ AI service direct test passed!")
            
        except Exception as e:
            print(f"❌ AI service test failed: {e}")
            raise

    @pytest.mark.asyncio(loop_scope="session")
    async def test_recipe_generation_integration(self, service_container: ServiceContainer):
        """Test recipe generation directly without WebSocket to verify recipe generation integration."""
        print("\n🍳 Testing recipe generation directly...")
        
        # Create user access
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        print(f"👤 Created user access: {user_access_data.user_id}")
        
        # Test recipe generation directly
        try:
            # Create a recipe generation request
            message_content = "Use the create_recipe tool to create a recipe for chocolate chip cookies"
            print(f"💬 Testing recipe generation with message: {message_content}")
            
            # Collect events to verify recipe generation is working
            events_received = []
            
            async def on_event(event):
                events_received.append(event)
                print(f"📥 Received event: {event.event}")
            
            # Test the AI service directly for recipe generation
            await service_container.ai_food_agent.stream_conversation(
                user_id=user_access_data.user_id,
                thread_id="test-recipe-thread",
                user_input=message_content,
                on_event=on_event
            )
            
            print(f"📊 Total events received: {len(events_received)}")
            
            # Verify we got some events
            assert len(events_received) > 0, "No events received from AI service"
            
            # Check for specific event types
            event_types = [event.event for event in events_received]
            print(f"📋 Event types received: {event_types}")
            
            # Should have recipe generation events
            assert "recipe_generation_started" in event_types, "No recipe generation started event"
            assert "recipe_generation_completed" in event_types, "No recipe generation completed event"
            
            # Should have recipe field detection events
            recipe_field_events = [e for e in events_received if e.event == "recipe_field_detected"]
            print(f"🍽️ Recipe field events received: {len(recipe_field_events)}")
            assert len(recipe_field_events) > 0, "No recipe field detection events"
            
            # Check for specific recipe fields
            field_names = [e.payload.field.name for e in recipe_field_events]
            print(f"📝 Recipe fields detected: {field_names}")
            
            # Should have essential recipe fields
            essential_fields = ["name", "ingredients", "instructions"]
            for field in essential_fields:
                assert field in field_names, f"Missing essential recipe field: {field}"
            
            # Get the completed recipe
            recipe_completed_events = [e for e in events_received if e.event == "recipe_generation_completed"]
            if recipe_completed_events:
                recipe = recipe_completed_events[0].payload.recipe
                print(f"🍳 Recipe name: {recipe.name}")
                print(f"🍳 Recipe ingredients: {len(recipe.ingredients)}")
                print(f"🍳 Recipe instructions: {len(recipe.instructions)}")
                
                # Verify recipe has required fields
                assert recipe.name, "Recipe name is empty"
                assert len(recipe.ingredients) > 0, "Recipe has no ingredients"
                assert len(recipe.instructions) > 0, "Recipe has no instructions"
                assert recipe.description, "Recipe description is empty"
                assert recipe.servings, "Recipe servings is empty"
            
            print("✅ Recipe generation direct test passed!")
            
        except Exception as e:
            print(f"❌ Recipe generation test failed: {e}")
            raise

    @pytest.mark.asyncio(loop_scope="session")
    async def test_search_integration(self, service_container: ServiceContainer):
        """Test search functionality directly without WebSocket to verify search integration."""
        print("\n🔍 Testing search functionality directly...")
        
        # Create user access
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        print(f"👤 Created user access: {user_access_data.user_id}")
        
        # Test search functionality directly
        try:
            # Create a search request that's more likely to trigger search
            message_content = "Search for the latest cooking trends in 2024"
            print(f"💬 Testing search with message: {message_content}")
            
            # Collect events to verify search is working
            events_received = []
            
            async def on_event(event):
                events_received.append(event)
                print(f"📥 Received event: {event.event}")
            
            # Test the AI service directly for search
            await service_container.ai_food_agent.stream_conversation(
                user_id=user_access_data.user_id,
                thread_id="test-search-thread",
                user_input=message_content,
                on_event=on_event
            )
            
            print(f"📊 Total events received: {len(events_received)}")
            
            # Verify we got some events
            assert len(events_received) > 0, "No events received from AI service"
            
            # Check for specific event types
            event_types = [event.event for event in events_received]
            print(f"📋 Event types received: {event_types}")
            
            # Check if search events were triggered
            has_search_events = "search_started" in event_types and "search_completed" in event_types
            
            if has_search_events:
                print("🔍 Search events detected!")
                
                # Check search details
                search_started_events = [e for e in events_received if e.event == "search_started"]
                search_completed_events = [e for e in events_received if e.event == "search_completed"]
                
                if search_started_events:
                    search_data = search_started_events[0].payload
                    print(f"🔍 Search tool: {search_data.tool_name}")
                    print(f"🔍 Search query: {search_data.tool_input}")
                
                if search_completed_events:
                    search_data = search_completed_events[0].payload
                    print(f"🔍 Search results received: {len(str(search_data.tool_output))} chars")
                    print(f"🔍 Search metadata: {search_data.tool_metadata.model_name}")
            else:
                print("ℹ️ No search events detected - AI may have answered without searching")
            
            # Should have text message events
            assert "text_message_started" in event_types, "No text message started event"
            assert "text_message_completed" in event_types, "No text message completed event"
            
            # Get the final response
            text_completed_events = [e for e in events_received if e.event == "text_message_completed"]
            if text_completed_events:
                # Get the last text message completed event (the final response after search)
                full_response = text_completed_events[-1].payload.full_message
                print(f"🤖 AI Response: {full_response[:100]}...")
                assert len(full_response) > 0, "AI response is empty"
            
            print("✅ Search direct test passed!")
            
        except Exception as e:
            print(f"❌ Search test failed: {e}")
            raise

    def test_basic_chat_websocket_flow(self, test_client, service_container):
        """Synchronous E2E test for real chat flow using TestClient and WebSocket."""
        print("\n🧪 Testing basic chat WebSocket flow (sync)...")

        # Create user access (sync wrapper)
        user_access_data = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        access_token = user_access_data.access_token
        print(f"🔑 Access token: {access_token[:20]}...")

        with test_client.websocket_connect(f"/ws/chat?access_token={access_token}") as websocket:
            # Send a user message
            message = {"id": "1", "content": "Hello! Can you help me with cooking?"}
            print(f"📤 Sending: {message}")
            websocket.send_json(message)

            # Collect events with simple timeout
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

            # Assert we got the expected events
            event_types = [e["event"] for e in events]
            print(f"📋 Event types: {event_types}")
            
            # Check if we captured thread title update
            if "thread_title_updated" in event_types:
                print("📝 Thread title updated event captured!")
                thread_title_events = [e for e in events if e["event"] == "thread_title_updated"]
                if thread_title_events:
                    thread_data = thread_title_events[0]["data"]
                    print(f"📝 New thread title: {thread_data.get('thread', {}).get('title', 'N/A')}")
            
            assert "text_message_started" in event_types
            assert "text_message_completed" in event_types
            # Optionally, check the content of the completed message
            text_completed_events = [e for e in events if e["event"] == "text_message_completed"]
            if text_completed_events:
                full_response = text_completed_events[0]["data"]["message"]["text_content"]
                print(f"🤖 AI Response: {full_response[:100]}...")
                assert len(full_response) > 0, "AI response is empty"
            print("✅ Basic chat WebSocket flow test passed!")

    def test_recipe_generation_websocket_flow(self, test_client, service_container):
        """Synchronous E2E test for recipe generation using TestClient and WebSocket."""
        print("\n🍳 Testing recipe generation WebSocket flow (sync)...")

        # Create user access (sync wrapper)
        user_access_data = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        access_token = user_access_data.access_token
        print(f"🔑 Access token: {access_token[:20]}...")

        with test_client.websocket_connect(f"/ws/chat?access_token={access_token}") as websocket:
            # Send a recipe generation request
            message = {"id": "1", "content": "Use the create_recipe tool to create a recipe for chocolate chip cookies"}
            print(f"📤 Sending: {message}")
            websocket.send_json(message)

            # Collect events with simple timeout
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
                        # The recipe field data is in the recipe object, not a direct field key
                        if "recipe" in event["data"]:
                            recipe_data = event["data"]["recipe"]
                            print(f"🍽️ Recipe field detected: recipe updated")
                    
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

            # Assert we got the expected events
            event_types = [e["event"] for e in events]
            print(f"📋 Event types: {event_types}")
            
            # Check if we captured thread title update
            if "thread_title_updated" in event_types:
                print("📝 Thread title updated event captured!")
                thread_title_events = [e for e in events if e["event"] == "thread_title_updated"]
                if thread_title_events:
                    thread_data = thread_title_events[0]["data"]
                    print(f"📝 New thread title: {thread_data.get('thread', {}).get('title', 'N/A')}")
            
            # Should have recipe generation events
            assert "recipe_generation_started" in event_types, "No recipe generation started event"
            assert "recipe_generation_completed" in event_types, "No recipe generation completed event"
            assert recipe_completed, "Recipe generation did not complete"
            
            # Should have recipe field detection events
            assert len(recipe_field_events) > 0, "No recipe field detection events"
            
            # Check the completed recipe
            recipe_completed_events = [e for e in events if e["event"] == "recipe_generation_completed"]
            if recipe_completed_events:
                recipe_data = recipe_completed_events[0]["data"]["recipe"]
                print(f"🍳 Recipe name: {recipe_data['name']}")
                print(f"🍳 Recipe ingredients: {len(recipe_data['ingredients'])}")
                print(f"🍳 Recipe instructions: {len(recipe_data['instructions'])}")
                
                # Verify recipe has required fields
                assert recipe_data["name"], "Recipe name is empty"
                assert len(recipe_data["ingredients"]) > 0, "Recipe has no ingredients"
                assert len(recipe_data["instructions"]) > 0, "Recipe has no instructions"
                assert recipe_data["description"], "Recipe description is empty"
                assert recipe_data["servings"], "Recipe servings is empty"
            
            print("✅ Recipe generation WebSocket flow test passed!")

    def test_search_websocket_flow(self, test_client: TestClient, service_container: ServiceContainer):
        """Synchronous E2E test for search functionality using TestClient and WebSocket."""
        print("\n🔍 Testing search WebSocket flow (sync)...")

        # Create user access (sync wrapper)
        user_access_data = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        access_token = user_access_data.access_token
        print(f"🔑 Access token: {access_token[:20]}...")

        with test_client.websocket_connect(f"/ws/chat?access_token={access_token}") as websocket:
            # Send a search request that's more likely to trigger search
            message = {"id": "1", "content": "Use search to find the latest cooking trends in 2024"}
            print(f"📤 Sending: {message}")
            websocket.send_json(message)

            # Collect events with simple timeout
            events = []
            max_events = 20
            search_completed = False
            final_response_completed = False
            
            for _ in range(max_events):
                try:
                    event = websocket.receive_json()
                    print(f"📥 Received event: {event['event']}")
                    events.append(event)
                    
                    # Track search completion
                    if event["event"] == "search_completed":
                        search_completed = True
                    
                    # Track when we get the final text_message_completed after search
                    if event["event"] == "text_message_completed" and search_completed and not final_response_completed:
                        final_response_completed = True
                        print(f"📥 Final response completed")
                        # Wait a bit for any additional events like thread_title_updated
                        time.sleep(1.0)
                        break
                        
                except Exception as e:
                    # No more events
                    print(f"📥 No more events: {e}")
                    break

            # Assert we got the expected events
            event_types = [e["event"] for e in events]
            print(f"📋 Event types: {event_types}")
            
            # Check if we captured thread title update
            if "thread_title_updated" in event_types:
                print("📝 Thread title updated event captured!")
                thread_title_events = [e for e in events if e["event"] == "thread_title_updated"]
                if thread_title_events:
                    thread_data = thread_title_events[0]["data"]
                    print(f"📝 New thread title: {thread_data.get('thread', {}).get('title', 'N/A')}")
            
            # Check if search events were triggered
            has_search_events = "search_started" in event_types and "search_completed" in event_types
            
            if has_search_events:
                print("🔍 Search events detected!")
                
                # Check search details
                search_started_events = [e for e in events if e["event"] == "search_started"]
                search_completed_events = [e for e in events if e["event"] == "search_completed"]
                
                if search_started_events:
                    search_data = search_started_events[0]["data"]
                    print(f"🔍 Search tool: {search_data.get('message', {}).get('tool_name', 'N/A')}")
                    print(f"🔍 Search query: {search_data.get('message', {}).get('tool_input', 'N/A')}")
                
                if search_completed_events:
                    search_data = search_completed_events[0]["data"]
                    print(f"🔍 Search results received: {len(str(search_data.get('message', {}).get('tool_output', '')))} chars")
                    print(f"🔍 Search metadata: {search_data.get('message', {}).get('model_name', 'N/A')}")
            else:
                print("ℹ️ No search events detected - AI may have answered without searching")
            
            # Should have text message events
            assert "text_message_started" in event_types, "No text message started event"
            assert "text_message_completed" in event_types, "No text message completed event"
            
            # Check the final response - should have content regardless of whether search was used
            text_completed_events = [e for e in events if e["event"] == "text_message_completed"]
            if text_completed_events:
                # Get the last text message completed event (the final response after search)
                full_response = text_completed_events[-1]["data"]["message"]["text_content"]
                print(f"🤖 AI Response: {full_response[:100]}...")
                assert len(full_response) > 0, "AI response is empty"
            
            print("✅ Search WebSocket flow test passed!")


class TestDataPersistence:
    def test_basic_chat_message_persistence_anonymous(self, test_client: TestClient, service_container: ServiceContainer):
        """Test that messages are persisted in cache for anonymous users after basic chat."""
        print("\n💾 Testing message persistence for anonymous user...")

        # Create anonymous user access
        user_access_data = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        access_token = user_access_data.access_token
        user_id = user_access_data.user_id
        print(f"🔑 Anonymous access token: {access_token[:20]}...")
        print(f"👤 Anonymous user ID: {user_id}")

        with test_client.websocket_connect(f"/ws/chat?access_token={access_token}") as websocket:
            # Send a user message
            message = {"id": "1", "content": "Hello! Can you help me with cooking?"}
            print(f"📤 Sending: {message}")
            websocket.send_json(message)

            # Collect events with simple timeout
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

            # Verify events were received
            event_types = [e["event"] for e in events]
            print(f"📋 Event types: {event_types}")
            assert "text_message_completed" in event_types, "No text message completed event"

        # Check that messages are stored in cache for anonymous user
        print(f"🔍 Checking cache for user {user_id}...")
        
        # Get thread from cache
        cached_threads = asyncio.get_event_loop().run_until_complete(
            service_container.thread_cache_service.get_threads(user_id)
        )
        print(f"📁 Cached threads: {len(cached_threads)}")
        assert len(cached_threads) == 1, "Expected 1 thread in cache"
        
        thread_id = cached_threads[0].id
        print(f"🧵 Thread ID: {thread_id}")
        
        # Get messages from cache
        cached_messages = asyncio.get_event_loop().run_until_complete(
            service_container.message_cache_service.get_messages_by_user_id(user_id)
        )
        print(f"💬 Cached messages: {len(cached_messages)}")
        assert len(cached_messages) == 2, "Expected 2 messages (user + AI) in cache"
        
        # Verify message content
        user_messages = [m for m in cached_messages if m.role == MessageRole.user.value]
        ai_messages = [m for m in cached_messages if m.role == MessageRole.assistant.value]
        
        print(f"👤 User messages: {len(user_messages)}")
        print(f"🤖 AI messages: {len(ai_messages)}")
        
        assert len(user_messages) >= 1, "No user messages found in cache"
        assert len(ai_messages) >= 1, "No AI messages found in cache"
        
        # Check user message content
        user_message = user_messages[0]
        print(f"👤 User message content: {user_message.text_content[:50]}...")
        assert "Hello! Can you help me with cooking?" in user_message.text_content
        
        # Check AI message content
        ai_message = ai_messages[0]
        print(f"🤖 AI message content: {ai_message.text_content[:50]}...")
        assert len(ai_message.text_content) > 0, "AI message is empty"
        
        print("✅ Anonymous user message persistence test passed!")

    def test_basic_chat_message_persistence_authenticated(self, test_client: TestClient, service_container: ServiceContainer):
        """Test that messages are persisted in database for authenticated users after basic chat."""
        print("\n💾 Testing message persistence for authenticated user...")

        # Create authenticated user access
        user_access_data = asyncio.get_event_loop().run_until_complete(
            service_container.user_access_cache_service.create_anonymous_access()
        )
        access_token = user_access_data.access_token
        user_id = user_access_data.user_id
        print(f"🔑 Access token: {access_token[:20]}...")
        print(f"👤 User ID: {user_id}")

        # Create a user in the database (simulate signup)
        async def create_user():
            async with service_container.db_transaction_maker() as db:
                user = await service_container.user_service.create_user(
                    db=db,
                    params=CreateUserParams(
                        email="test@example.com",
                        name="Test User",
                        password="hashed_password",
                        id=user_access_data.user_id,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                )
                # Update the access token to be authenticated
                await service_container.user_access_cache_service.promote_to_authenticated(
                    access_token=access_token,
                    user_id=user.id,
                    email=user.email,
                    name=user.name
                )
                return user
        
        user = asyncio.get_event_loop().run_until_complete(create_user())
        print(f"👤 Created authenticated user: {user.id}")

        with test_client.websocket_connect(f"/ws/chat?access_token={access_token}") as websocket:
            # Send a user message
            message = {"id": "1", "content": "Hello! Can you help me with cooking?"}
            print(f"📤 Sending: {message}")
            websocket.send_json(message)

            # Collect events with simple timeout
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

            # Verify events were received
            event_types = [e["event"] for e in events]
            print(f"📋 Event types: {event_types}")
            assert "text_message_completed" in event_types, "No text message completed event"

        # Check that messages are stored in database for authenticated user
        print(f"🔍 Checking database for user {user.id}...")
        
        # Get thread from database
        async def check_database():
            async with service_container.db_transaction_maker() as db:
                # Get threads from database
                db_threads = await service_container.thread_service.get_paginated_threads(
                    db, 
                    GetUserThreadsParams(user_id=user.id)
                )
                print(f"📁 Database threads: {len(db_threads.threads)}")
                assert len(db_threads.threads) > 0, "No threads found in database"
                
                thread_id = db_threads.threads[0].id
                print(f"🧵 Thread ID: {thread_id}")
                
                # Get messages from database
                db_messages = await service_container.message_service.get_paginated_messages(
                    db,
                    GetMessagesParams(thread_id=thread_id)
                )
                print(f"💬 Database messages: {len(db_messages.messages)}")
                assert len(db_messages.messages) >= 2, "Expected at least 2 messages (user + AI) in database"
                
                # Verify message content
                user_messages = [m for m in db_messages.messages if m.role == MessageRole.user.value]
                ai_messages = [m for m in db_messages.messages if m.role == MessageRole.assistant.value]
                
                print(f"👤 User messages: {len(user_messages)}")
                print(f"🤖 AI messages: {len(ai_messages)}")
                
                assert len(user_messages) >= 1, "No user messages found in database"
                assert len(ai_messages) >= 1, "No AI messages found in database"
                
                # Check user message content
                user_message = user_messages[0]
                print(f"👤 User message content: {user_message.text_content[:50]}...")
                assert "Hello! Can you help me with cooking?" in user_message.text_content
                
                # Check AI message content
                ai_message = ai_messages[0]
                print(f"🤖 AI message content: {ai_message.text_content[:50]}...")
                assert len(ai_message.text_content) > 0, "AI message is empty"
        
        asyncio.get_event_loop().run_until_complete(check_database())
        
        print("✅ Authenticated user message persistence test passed!") 