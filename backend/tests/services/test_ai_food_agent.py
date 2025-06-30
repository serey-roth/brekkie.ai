import os
from unittest.mock import MagicMock, AsyncMock, patch, call
import pytest

os.environ["TAVILY_API_KEY"] = "mock_tavily_key"
os.environ["GOOGLE_API_KEY"] = "mock_google_api_key"

from langchain_core.messages import AIMessageChunk, ToolMessage

from schemas.conversation_stream_events import (
    TextMessageCompletedPayload,
    ConversationStreamEvent, 
    TextMessageStartedPayload, 
    TextMessageChunkGeneratedPayload,
    ConversationStreamMetadata,
    RecipeGenerationStartedPayload, 
    RecipeFieldDetectedPayload,
    RecipeGenerationCompletedPayload,
    SearchStartedPayload,
    SearchCompletedPayload,
)

from schemas.recipes import (
    RecipeCategory,
    RecipeIngredient,
    RecipeInstruction,
    Recipe,
    RecipeField,
)

from src.services.ai_food_agent.google_ai_food_agent import GoogleAIFoodAgent

from tests.utils.assert_deep_equal import assert_deep_equal


@pytest.fixture
def mock_checkpointer():
    mock_checkpointer = MagicMock()
    return mock_checkpointer

@pytest.fixture
def mock_agent_service(mock_checkpointer):
    mock_agent_service = GoogleAIFoodAgent(mock_checkpointer)
    return mock_agent_service


def basic_response_events():
    return [ 
        ("messages", (AIMessageChunk(content="Hello"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 6})),
        ("messages", (AIMessageChunk(content=" there"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 4})),
        ("messages", (AIMessageChunk(content="!"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 1})),
    ]
    
def recipe_generation_events():
    return [
        ("messages", (AIMessageChunk(content="I'll create a recipe for you."), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 10})),
        ("custom", {"event": "recipe_generation_started", "tool_name": "create_recipe", "tool_input": {"idea": "Pasta Carbonara", "context": "A delicious pasta dish with eggs and bacon"}}),
        ("messages", (AIMessageChunk(content="<recipe><name>Pasta Carbonara</name>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 5})),
        ("messages", (AIMessageChunk(content="<description>A delicious pasta dish with eggs and bacon</description>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 8})),
        ("messages", (AIMessageChunk(content="<prep_time_minutes>10</prep_time_minutes>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 3})),
        ("messages", (AIMessageChunk(content="<cook_time_minutes>15</cook_time_minutes>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 3})),
        ("messages", (AIMessageChunk(content="<servings>2</servings>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 2})),
        ("messages", (AIMessageChunk(content="<categories><category><cat_name>Italian</cat_name></category></categories>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 4})),
        ("messages", (AIMessageChunk(content="<ingredients>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 1})),
        ("messages", (AIMessageChunk(content="<ingredient><ing_name>pasta</ing_name><ing_quantity>100</ing_quantity><ing_unit>g</ing_unit></ingredient>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 6})),
        ("messages", (AIMessageChunk(content="<ingredient><ing_name>eggs</ing_name><ing_quantity>2</ing_quantity><ing_unit>pcs</ing_unit></ingredient>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 6})),
        ("messages", (AIMessageChunk(content="<ingredient><ing_name>bacon</ing_name><ing_quantity>100</ing_quantity><ing_unit>g</ing_unit></ingredient>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 6})),
        ("messages", (AIMessageChunk(content="</ingredients>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 1})),
        ("messages", (AIMessageChunk(content="<instructions>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 1})),
        ("messages", (AIMessageChunk(content="<instruction><ins_title>Boil pasta</ins_title><ins_description>Boil pasta in water</ins_description></instruction>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 8})),
        ("messages", (AIMessageChunk(content="<instruction><ins_title>Mix eggs and bacon</ins_title><ins_description>Mix eggs and bacon in a bowl</ins_description></instruction>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 8})),
        ("messages", (AIMessageChunk(content="</instructions>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 1})),
        ("messages", (AIMessageChunk(content="</recipe>"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 1})),
        ("messages", (ToolMessage(content='{"content": "<recipe>...</recipe>", "response_metadata": {"model_name": "gemini-2.5-flash-preview-05-20"}, "usage_metadata": {"input_tokens": 0, "output_tokens": 100}}', tool_call_id="123", name="create_recipe", status="success"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 100})),
    ]
    
def search_events():
    return [
        ("messages", (AIMessageChunk(content="I'll search the web for you."), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 10})),
        ("custom", {"event": "search_started", "tool_name": "tavily_search", "tool_input": {"query": "Pasta Carbonara"}}),
        ("messages", (ToolMessage(content='{"content": "<search_results>...</search_results>", "response_metadata": {"model_name": "gemini-2.5-flash-preview-05-20"}, "usage_metadata": {"input_tokens": 0, "output_tokens": 100}}', tool_call_id="123", name="tavily_search", status="success"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 100})),
    ]


def setup_mock_factory(events):
    async def mock_astream(*args, **kwargs):
        for event in events:
            yield event

    mock_agent = MagicMock()
    mock_agent.astream = mock_astream

    factory_instance = MagicMock()
    factory_instance.build.return_value = mock_agent

    return factory_instance


@pytest.fixture
def mock_event_handler():
    mock_event_handler = AsyncMock()
    return mock_event_handler

@pytest.fixture(autouse=True)
def setup_test_environment():
    original_tavily_key = os.environ.get("TAVILY_API_KEY")
    original_gemini_key = os.environ.get("GOOGLE_API_KEY")
    
    os.environ["TAVILY_API_KEY"] = "mock_tavily_key"
    os.environ["GOOGLE_API_KEY"] = "mock_gemini_key"
    
    yield
    
    if original_tavily_key is not None:
        os.environ["TAVILY_API_KEY"] = original_tavily_key
    else:
        os.environ.pop("TAVILY_API_KEY", None)
        
    if original_gemini_key is not None:
        os.environ["GOOGLE_API_KEY"] = original_gemini_key
    else:
        os.environ.pop("GOOGLE_API_KEY", None)


def test_get_agent_config(mock_agent_service):
    config = mock_agent_service.get_agent_config("user_id", "thread_id")
    assert_deep_equal(config, {
        "configurable": {"user_id": "user_id", "thread_id": "thread_id"},
        "tags": ["food_agent"],
        "metadata": {"thread_id": "thread_id"}
    })
    

class TestExtractMetadata:
    def test_extract_text_from_chunk(self, mock_agent_service):
        text = mock_agent_service.extract_text_from_chunk(AIMessageChunk(content="Hello"))
        assert text == "Hello"
        
        text = mock_agent_service.extract_text_from_chunk(AIMessageChunk(content=["Hello", " there"]))
        assert text == "Hello there"
        
    def test_extract_ai_chunk_metadata(self, mock_agent_service):
        chunk1 = AIMessageChunk(content="Hello")
        chunk1.usage_metadata = {"input_tokens": 0, "output_tokens": 6}
        metadata = mock_agent_service._extract_ai_chunk_metadata(chunk1, {"ls_model_name": "gemini-2.5-flash-preview-05-20"})
        assert_deep_equal(metadata, ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=6))
        
        chunk2 = AIMessageChunk(content=["Hello", " there"])
        chunk2.usage_metadata = {"input_tokens": 0, "output_tokens": 10}
        metadata = mock_agent_service._extract_ai_chunk_metadata(chunk2, {"ls_model_name": "gemini-2.5-flash-preview-05-20"})
        assert_deep_equal(metadata, ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=10))

    def test_extract_recipe_tool_message_metadata(self, mock_agent_service):
        tool_output, metadata = mock_agent_service._extract_recipe_tool_message_metadata(ToolMessage(content='{"content": "<recipe>...</recipe>", "response_metadata": {"model_name": "gemini-2.5-flash-preview-05-20"}, "usage_metadata": {"input_tokens": 0, "output_tokens": 100}}', tool_call_id="123", name="create_recipe", status="success"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 100})
        assert_deep_equal(tool_output, {"recipe_xml": "<recipe>...</recipe>"})
        assert_deep_equal(metadata, ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100))

    def test_extract_search_tool_message_metadata(self, mock_agent_service):
        tool_output, metadata = mock_agent_service._extract_search_tool_message_metadata(ToolMessage(content='{"content": "<search_results>...</search_results>", "response_metadata": {"model_name": "gemini-2.5-flash-preview-05-20"}, "usage_metadata": {"input_tokens": 0, "output_tokens": 100}}', tool_call_id="123", name="tavily_search", status="success"), {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 100})
        assert_deep_equal(tool_output, {"content": "<search_results>...</search_results>", "response_metadata": {"model_name": "gemini-2.5-flash-preview-05-20"}, "usage_metadata": {"input_tokens": 0, "output_tokens": 100}})
        assert_deep_equal(metadata, ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100))


class TestHandleToolMessage:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.mock_on_event = AsyncMock()
        self.mock_state = MagicMock()
        self.mock_recipe_parser = MagicMock()
        self.mock_recipe_parser.get_recipe.return_value = None
        self.mock_recipe_parser.get_recipe.return_value = MagicMock(spec=Recipe)
    
    @pytest.mark.asyncio
    async def test_handle_recipe_tool_message(self, mock_agent_service):
        food_agent = mock_agent_service
    
        mock_tool_message = ToolMessage(content='{"content": "<recipe>...</recipe>", "response_metadata": {"model_name": "gemini-2.5-flash-preview-05-20"}, "usage_metadata": {"input_tokens": 0, "output_tokens": 100}}', tool_call_id="123", name="create_recipe", status="success")
        mock_metadata = {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 100}
        
        await food_agent._handle_tool_message(mock_tool_message, mock_metadata, self.mock_recipe_parser, self.mock_state, self.mock_on_event)
        
        self.mock_on_event.assert_has_calls([
            call(ConversationStreamEvent(event="recipe_generation_completed", payload=RecipeGenerationCompletedPayload(
                recipe=self.mock_recipe_parser.get_recipe(),
                tool_output={"recipe_xml": "<recipe>...</recipe>"},
                tool_metadata=ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100),
            ))),
        ])
        
        self.mock_state.end_recipe_generation.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_search_tool_message(self, mock_agent_service):
        food_agent = mock_agent_service
    
        mock_tool_message = ToolMessage(content='{"content": "<search_results>...</search_results>", "response_metadata": {"model_name": "gemini-2.5-flash-preview-05-20"}, "usage_metadata": {"input_tokens": 0, "output_tokens": 100}}', tool_call_id="123", name="tavily_search", status="success")
        mock_metadata = {"ls_model_name": "gemini-2.5-flash-preview-05-20", "input_tokens": 0, "output_tokens": 100}
        
        await food_agent._handle_tool_message(mock_tool_message, mock_metadata, self.mock_recipe_parser, self.mock_state, self.mock_on_event)
        
        self.mock_on_event.assert_has_calls([
            call(ConversationStreamEvent(event="search_completed", payload=SearchCompletedPayload(
                tool_output={"content": "<search_results>...</search_results>", "response_metadata": {"model_name": "gemini-2.5-flash-preview-05-20"}, "usage_metadata": {"input_tokens": 0, "output_tokens": 100}},
                tool_metadata=ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100),
            ))),
        ])
    
    
class TestStreamConversation:
    @pytest.mark.asyncio
    async def test_message_stream(self, mock_agent_service, mock_event_handler):
        food_agent = mock_agent_service

        with patch("src.services.ai_food_agent.google_ai_food_agent.AgentFactory") as factory_patch, \
            patch.object(food_agent, "_extract_ai_chunk_metadata") as mock_extract_ai_chunk_metadata:
                
            mock_metadata = MagicMock(spec=ConversationStreamMetadata)
            mock_extract_ai_chunk_metadata.return_value = mock_metadata

            factory_patch.return_value = setup_mock_factory(basic_response_events())
            
            await food_agent.stream_conversation(
                "user_id",
                "thread_id",
                "user_input",
                on_event=mock_event_handler,
            )
            
            mock_event_handler.assert_has_calls([
                call(ConversationStreamEvent(event="text_message_started", payload=TextMessageStartedPayload())),
                call(ConversationStreamEvent(event="text_message_chunk_generated", payload=TextMessageChunkGeneratedPayload(
                    message_chunk="Hello",
                    metadata=mock_metadata,
                ))),
                call(ConversationStreamEvent(event="text_message_chunk_generated", payload=TextMessageChunkGeneratedPayload(
                    message_chunk=" there",
                    metadata=mock_metadata,
                ))),
                call(ConversationStreamEvent(event="text_message_chunk_generated", payload=TextMessageChunkGeneratedPayload(
                    message_chunk="!",
                    metadata=mock_metadata,
                ))),
                call(ConversationStreamEvent(event="text_message_completed", payload=TextMessageCompletedPayload(
                    full_message="Hello there!",
                ))),
            ])

    @pytest.mark.asyncio
    async def test_recipe_generation(self, mock_agent_service, mock_event_handler):
        food_agent = mock_agent_service
        
        with patch("src.services.ai_food_agent.google_ai_food_agent.AgentFactory") as factory_patch, \
            patch.object(food_agent, "_extract_ai_chunk_metadata") as mock_extract_ai_chunk_metadata, \
            patch.object(food_agent, "_extract_recipe_tool_message_metadata") as mock_extract_recipe_tool_message_metadata:
                
            mock_metadata = MagicMock(spec=ConversationStreamMetadata)
            mock_extract_ai_chunk_metadata.return_value = mock_metadata
            
            mock_recipe_tool_output = MagicMock(spec=dict)
            mock_recipe_metadata = MagicMock(spec=ConversationStreamMetadata)
            mock_extract_recipe_tool_message_metadata.return_value = (mock_recipe_tool_output, mock_recipe_metadata)

            factory_patch.return_value = setup_mock_factory(recipe_generation_events())

            await food_agent.stream_conversation(
                "user_id",
                "thread_id",
                "user_input",
                on_event=mock_event_handler,
            )

            mock_event_handler.assert_has_calls([
                call(ConversationStreamEvent(event="text_message_started", payload=TextMessageStartedPayload())),
                call(ConversationStreamEvent(event="text_message_chunk_generated", payload=TextMessageChunkGeneratedPayload(
                    message_chunk="I'll create a recipe for you.",
                    metadata=mock_metadata,
                ))),
                call(ConversationStreamEvent(event="text_message_completed", payload=TextMessageCompletedPayload(
                    full_message="I'll create a recipe for you.",
                ))),
                call(ConversationStreamEvent(event="recipe_generation_started", payload=RecipeGenerationStartedPayload(
                    tool_name="create_recipe",
                    tool_input={"idea": "Pasta Carbonara", "context": "A delicious pasta dish with eggs and bacon"},
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="name",
                        value="Pasta Carbonara",
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="description",   
                        value="A delicious pasta dish with eggs and bacon",
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="prep_time_minutes",
                        value=10,
                    )
                ))),        
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="cook_time_minutes",
                        value=15,
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="servings",
                        value="2",
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="category",
                        value=RecipeCategory(name="Italian"),
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="categories",
                        value=[RecipeCategory(name="Italian")],
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="ingredient",
                        value=RecipeIngredient(
                            name="pasta",
                            quantity="100",
                            unit="g",
                        )
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="ingredient",
                        value=RecipeIngredient(
                            name="eggs",
                            quantity="2",
                            unit="pcs",
                        )
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="ingredient",
                        value=RecipeIngredient(
                            name="bacon",
                            quantity="100",
                            unit="g",
                        )
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="ingredients",
                        value=[
                            RecipeIngredient(name="pasta", quantity="100", unit="g"),
                            RecipeIngredient(name="eggs", quantity="2", unit="pcs"),
                            RecipeIngredient(name="bacon", quantity="100", unit="g")
                        ],
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="instruction",
                        value=RecipeInstruction(
                            title="Boil pasta",
                            description="Boil pasta in water",
                        )
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(     
                    field=RecipeField(
                        name="instruction",
                        value=RecipeInstruction(
                            title="Mix eggs and bacon",
                            description="Mix eggs and bacon in a bowl",
                        )
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_field_detected", payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="instructions",
                        value=[
                            RecipeInstruction(title="Boil pasta", description="Boil pasta in water"),   
                            RecipeInstruction(title="Mix eggs and bacon", description="Mix eggs and bacon in a bowl"),
                        ],
                    )
                ))),
                call(ConversationStreamEvent(event="recipe_generation_completed", payload=RecipeGenerationCompletedPayload(
                    recipe=Recipe(
                        name="Pasta Carbonara",         
                        description="A delicious pasta dish with eggs and bacon",
                        prep_time_minutes=10,
                        cook_time_minutes=15,
                        servings="2",
                        categories=[RecipeCategory(name="Italian")],
                        ingredients=[   
                            RecipeIngredient(name="pasta", quantity="100", unit="g"),
                            RecipeIngredient(name="eggs", quantity="2", unit="pcs"),
                            RecipeIngredient(name="bacon", quantity="100", unit="g")
                        ],
                        instructions=[
                            RecipeInstruction(title="Boil pasta", description="Boil pasta in water"),   
                            RecipeInstruction(title="Mix eggs and bacon", description="Mix eggs and bacon in a bowl")
                        ]),
                    tool_output=mock_recipe_tool_output,
                    tool_metadata=mock_recipe_metadata, 
                ))),
            ])
            
    @pytest.mark.asyncio
    async def test_search(self, mock_agent_service, mock_event_handler):
        food_agent = mock_agent_service
        
        with patch("src.services.ai_food_agent.google_ai_food_agent.AgentFactory") as factory_patch, \
            patch.object(food_agent, "_extract_ai_chunk_metadata") as mock_extract_ai_chunk_metadata, \
            patch.object(food_agent, "_extract_search_tool_message_metadata") as mock_extract_search_tool_message_metadata:
                
            mock_metadata = MagicMock(spec=ConversationStreamMetadata)
            mock_extract_ai_chunk_metadata.return_value = mock_metadata
            
            mock_search_tool_output = MagicMock(spec=dict)
            mock_search_metadata = MagicMock(spec=ConversationStreamMetadata)
            mock_extract_search_tool_message_metadata.return_value = (mock_search_tool_output, mock_search_metadata)
            
            factory_patch.return_value = setup_mock_factory(search_events())
            
            await food_agent.stream_conversation(
                "user_id",
                "thread_id",
                "user_input",
                on_event=mock_event_handler,
            )
            
            mock_event_handler.assert_has_calls([
                call(ConversationStreamEvent(event="text_message_started", payload=TextMessageStartedPayload())),
                call(ConversationStreamEvent(event="text_message_chunk_generated", payload=TextMessageChunkGeneratedPayload(
                    message_chunk="I'll search the web for you.",
                    metadata=mock_metadata,
                ))),
                call(ConversationStreamEvent(event="text_message_completed", payload=TextMessageCompletedPayload(
                    full_message="I'll search the web for you.",
                ))),
                call(ConversationStreamEvent(event="search_started", payload=SearchStartedPayload(
                    tool_name="tavily_search",
                    tool_input={"query": "Pasta Carbonara"},
                ))),
                call(ConversationStreamEvent(event="search_completed", payload=SearchCompletedPayload(
                    tool_output=mock_search_tool_output,
                    tool_metadata=mock_search_metadata,
                ))),
            ])