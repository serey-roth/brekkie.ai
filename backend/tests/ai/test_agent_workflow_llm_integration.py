import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
env_file = os.path.join(backend_dir, '.env.test')

from dotenv import load_dotenv
load_dotenv(env_file)

import pytest
from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from ai.workflow.agent import AgentFactory, AgentState


@pytest.fixture
def mock_checkpointer():
    return InMemorySaver()


@pytest.fixture
def agent_factory(mock_checkpointer):
    return AgentFactory(
        user_id="test_user",
        thread_id="test_thread",
        checkpointer=mock_checkpointer
    )


class TestUpdateThreadTitleRealLLM:
    """Tests using real Gemini API to see actual errors"""
    
    @pytest.mark.asyncio
    async def test_update_thread_title_with_normal_messages(self, agent_factory):
        """Test thread title update with normal conversation messages"""
        messages = [
            HumanMessage(content="I need help with dinner tonight"),
            AIMessage(content="I'd be happy to help you with dinner! What kind of food are you in the mood for?"),
            HumanMessage(content="I'm thinking something Italian, maybe pasta"),
            AIMessage(content="Great choice! I can suggest a few Italian pasta dishes. Do you have any dietary restrictions or preferences?"),
            HumanMessage(content="I'm vegetarian, so no meat please"),
        ]
        
        state = AgentState(messages=messages) # type: ignore
        
        with patch('ai.workflow.agent.get_stream_writer') as mock_writer:
            mock_write = MagicMock()
            mock_writer.return_value = mock_write
            
            result = await agent_factory.update_thread_title(state)
            print(f"✅ Success! Thread title: {result.get('thread_title', 'N/A')}")
            assert result is not None
            assert "thread_title" in result
            assert len(result["thread_title"]) > 0

    @pytest.mark.asyncio
    async def test_update_thread_title_with_tool_messages(self, agent_factory):
        """Test thread title update with tool messages containing recipe data"""
        messages = [
            HumanMessage(content="I want a recipe for pasta carbonara"),
            AIMessage(content="I'll create a recipe for you."),
            ToolMessage(
                content='{"content": "<recipe><name>Pasta Carbonara</name><description>A delicious pasta dish</description><ingredients><ingredient><ing_name>pasta</ing_name><ing_quantity>100</ing_quantity><ing_unit>g</ing_unit></ingredient><ingredient><ing_name>eggs</ing_name><ing_quantity>2</ing_quantity><ing_unit>pcs</ing_unit></ingredient><ingredient><ing_name>bacon</ing_name><ing_quantity>100</ing_quantity><ing_unit>g</ing_unit></ingredient></ingredients><instructions><instruction><ins_title>Boil pasta</ins_title><ins_description>Boil pasta in water</ins_description></instruction><instruction><ins_title>Mix eggs and bacon</ins_title><ins_description>Mix eggs and bacon in a bowl</ins_description></instruction></instructions></recipe>", "response_metadata": {"model_name": "gemini-2.5-flash-preview-05-20"}, "usage_metadata": {"input_tokens": 0, "output_tokens": 100}}',
                tool_call_id="123",
            ),
            HumanMessage(content="That looks great! Can you make it vegetarian?"),
        ]
        
        state = AgentState(messages=messages) # type: ignore
        
        with patch('ai.workflow.agent.get_stream_writer') as mock_writer:
            mock_write = MagicMock()
            mock_writer.return_value = mock_write
            
            result = await agent_factory.update_thread_title(state)
            print(f"✅ Success with tool messages! Thread title: {result.get('thread_title', 'N/A')}")
            assert result is not None
            assert "thread_title" in result
            assert len(result["thread_title"]) > 0

    @pytest.mark.asyncio
    async def test_update_thread_title_with_special_characters(self, agent_factory):
        """Test thread title update with messages containing special characters and emojis"""
        messages = [
            HumanMessage(content="I want a recipe with 🍝 and 🧀"),
            AIMessage(content="I'll help you create a delicious pasta dish with cheese!"),
            HumanMessage(content="Can you make it gluten-free? 🌾"),
        ]
        
        state = AgentState(messages=messages) # type: ignore
        
        with patch('ai.workflow.agent.get_stream_writer') as mock_writer:
            mock_write = MagicMock()
            mock_writer.return_value = mock_write
                
            result = await agent_factory.update_thread_title(state)
            print(f"✅ Success with special characters! Thread title: {result.get('thread_title', 'N/A')}")
            assert result is not None
            assert "thread_title" in result
            assert len(result["thread_title"]) > 0

    @pytest.mark.asyncio
    async def test_update_thread_title_empty_messages(self, agent_factory):
        """Test thread title update with empty message list"""
        state = AgentState(messages=[]) # type: ignore
        
        with patch('ai.workflow.agent.get_stream_writer') as mock_writer:
            mock_write = MagicMock()
            mock_writer.return_value = mock_write
            
            result = await agent_factory.update_thread_title(state)
            print(f"✅ Success with empty messages! Thread title: {result.get('thread_title', 'N/A')}")
            assert result is not None
            assert "thread_title" in result
            assert len(result["thread_title"]) > 0

    @pytest.mark.asyncio
    async def test_update_thread_title_with_mixed_content_types(self, agent_factory):
        """Test thread title update with a mix of different content types"""
        messages = [
            HumanMessage(content="I need help with dinner"),
            AIMessage(content="I'll help you create a recipe!"),
            ToolMessage(
                content='{"content": "<recipe><name>Quick Pasta</name></recipe>", "response_metadata": {"model_name": "gemini-2.5-flash-preview-05-20"}, "usage_metadata": {"input_tokens": 0, "output_tokens": 50}}',
                tool_call_id="123",
            ),
            HumanMessage(content="That looks great! Can you make it vegetarian?"),
            AIMessage(content="Absolutely! I'll modify the recipe to be vegetarian."),
            ToolMessage(
                content='{"content": "<recipe><name>Vegetarian Quick Pasta</name></recipe>", "response_metadata": {"model_name": "gemini-2.5-flash-preview-05-20"}, "usage_metadata": {"input_tokens": 0, "output_tokens": 50}}',
                tool_call_id="124",
                name="create_recipe",
                status="success"
            ),
        ]
        
        state = AgentState(messages=messages) # type: ignore
        
        with patch('ai.workflow.agent.get_stream_writer') as mock_writer:
            mock_write = MagicMock()
            mock_writer.return_value = mock_write
            
            result = await agent_factory.update_thread_title(state)
            print(f"✅ Success with mixed content types! Thread title: {result.get('thread_title', 'N/A')}")
            assert result is not None
            assert "thread_title" in result
            assert len(result["thread_title"]) > 0
    
    @pytest.mark.asyncio
    async def test_update_thread_title_with_ai_message_as_last_message(self, agent_factory):
        """Test thread title update with only AI message as last message"""
        messages = [
            AIMessage(content="I'll help you!"),
        ]
        
        state = AgentState(messages=messages) # type: ignore
        
        with patch('ai.workflow.agent.get_stream_writer') as mock_writer:
            mock_write = MagicMock()
            mock_writer.return_value = mock_write
            
            result = await agent_factory.update_thread_title(state)
            print(f"✅ Success with AI message only! Thread title: {result.get('thread_title', 'N/A')}")
            assert result is not None
            assert "thread_title" in result
            assert len(result["thread_title"]) > 0
            
    @pytest.mark.asyncio
    async def test_update_thread_title_with_tool_message_as_last_message(self, agent_factory):
        """Test thread title update with only tool message as last message"""
        messages = [
            ToolMessage(
                content='{"content": "<recipe><name>Pasta Carbonara</name></recipe>", "response_metadata": {"model_name": "gemini-2.5-flash-preview-05-20"}, "usage_metadata": {"input_tokens": 0, "output_tokens": 50}}',
                tool_call_id="123",
            ),
        ]
        
        state = AgentState(messages=messages) # type: ignore
        
        with patch('ai.workflow.agent.get_stream_writer') as mock_writer:
            mock_write = MagicMock()
            mock_writer.return_value = mock_write
            
            result = await agent_factory.update_thread_title(state)
            print(f"✅ Success with tool message only! Thread title: {result.get('thread_title', 'N/A')}")
            assert result is not None
            assert "thread_title" in result
            assert len(result["thread_title"]) > 0