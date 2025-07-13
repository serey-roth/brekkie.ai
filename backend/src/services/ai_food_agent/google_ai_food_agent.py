from typing import Callable, Awaitable, Dict, Any
import json

from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.messages import HumanMessage, ToolMessage, AIMessageChunk

from ai.workflow.agent import AgentFactory

from services.ai_food_agent.ai_food_agent import AIFoodAgent
from services.streaming_recipe_parser.streaming_recipe_parser import StreamingRecipeFieldParser

from schemas.conversation_stream_state import ConversationStreamState
from schemas.conversation_stream_events import (
    ConversationStreamEvent,
    TextMessageStartedPayload,
    TextMessageChunkGeneratedPayload,
    TextMessageCompletedPayload,
    SearchStartedPayload,
    SearchCompletedPayload,
    RecipeGenerationStartedPayload,
    RecipeFieldDetectedPayload,
    RecipeGenerationCompletedPayload,
    AIAgentErrorPayload,
    SummaryUpdatedPayload,
    ThreadTitleUpdatedPayload,
    ConversationStreamMetadata,
)

from utils.logger import Logger

logger = Logger("google_ai_food_agent")


class GoogleAIFoodAgent(AIFoodAgent):
    def __init__(self, checkpointer: BaseCheckpointSaver):
        super().__init__(checkpointer)

    def _extract_ai_chunk_metadata(
        self, chunk: AIMessageChunk, metadata: Dict[str, Any]
    ) -> ConversationStreamMetadata:
        usage_metadata = chunk.usage_metadata or {}
        return ConversationStreamMetadata(
            model_name=metadata.get("ls_model_name", "unknown"),
            input_tokens=usage_metadata.get("input_tokens", 0),
            output_tokens=usage_metadata.get("output_tokens", 0),
        )

    def _extract_recipe_tool_message_metadata(
        self, tool_message: ToolMessage, metadata: Dict[str, Any]
    ) -> tuple[dict, ConversationStreamMetadata]:
        try:
            # TODO: Weird but somehow the tool message content is a stringified JSON object of the tool result
            content = tool_message.content
            if isinstance(content, str):
                inner_metadata = json.loads(content)
            else:
                inner_metadata = {}
        except json.JSONDecodeError:
            inner_metadata = {}

        tool_output = {"recipe_xml": inner_metadata.get("content", tool_message.content)}
        response_metadata = inner_metadata.get("response_metadata", {})
        usage_metadata = inner_metadata.get("usage_metadata", {})

        return tool_output, ConversationStreamMetadata(
            model_name=response_metadata.get("model_name", "unknown"),
            input_tokens=usage_metadata.get("input_tokens", 0),
            output_tokens=usage_metadata.get("output_tokens", 0),
        )

    def _extract_search_tool_message_metadata(
        self, tool_message: ToolMessage, metadata: Dict[str, Any]
    ) -> tuple[dict, ConversationStreamMetadata]:
        # content is Tavily search results in JSON format
        content = tool_message.content
        if isinstance(content, str):
            tool_output = json.loads(content)
        else:
            tool_output = {}
        return tool_output, ConversationStreamMetadata(
            model_name=metadata.get("ls_model_name", "unknown"),
            input_tokens=metadata.get("input_tokens", 0),
            output_tokens=metadata.get("output_tokens", 0),
        )

    async def _handle_tool_message(
        self,
        tool_message: ToolMessage,
        metadata: Dict[str, Any],
        recipe_parser: StreamingRecipeFieldParser,
        state: ConversationStreamState,
        on_event: Callable[[ConversationStreamEvent], Awaitable[None]],
    ):
        if tool_message.name == "create_recipe":
            tool_output, tool_metadata = self._extract_recipe_tool_message_metadata(
                tool_message, metadata
            )
            await on_event(
                ConversationStreamEvent(
                    event="recipe_generation_completed",
                    payload=RecipeGenerationCompletedPayload(
                        recipe=recipe_parser.get_recipe(),
                        tool_output=tool_output,
                        tool_metadata=tool_metadata,
                    ),
                )
            )
            state.end_recipe_generation()
        elif tool_message.name == "tavily_search":
            tool_output, tool_metadata = self._extract_search_tool_message_metadata(
                tool_message, metadata
            )
            await on_event(
                ConversationStreamEvent(
                    event="search_completed",
                    payload=SearchCompletedPayload(
                        tool_output=tool_output, tool_metadata=tool_metadata
                    ),
                )
            )
            state.end_search()
        else:
            logger.error(f"Unexpected tool message: {tool_message.name}")

    async def _handle_ai_message_start(
        self,
        state: ConversationStreamState,
        on_event: Callable[[ConversationStreamEvent], Awaitable[None]],
    ):
        await on_event(
            ConversationStreamEvent(
                event="text_message_started", payload=TextMessageStartedPayload()
            )
        )
        state.start_message_stream()

    async def _handle_ai_message_chunk(
        self,
        chunk: AIMessageChunk,
        metadata: Dict[str, Any],
        state: ConversationStreamState,
        recipe_parser: StreamingRecipeFieldParser,
        on_event: Callable[[ConversationStreamEvent], Awaitable[None]],
    ):
        chunk_metadata = self._extract_ai_chunk_metadata(chunk, metadata)
        text = self.extract_text_from_chunk(chunk)

        if state.has_recipe_generation_started():
            results = recipe_parser.feed(text)
            for field in results:
                await on_event(
                    ConversationStreamEvent(
                        event="recipe_field_detected",
                        payload=RecipeFieldDetectedPayload(field=field),
                    )
                )
        else:
            # This must be a text message chunk since search results are complete JSON objects
            await on_event(
                ConversationStreamEvent(
                    event="text_message_chunk_generated",
                    payload=TextMessageChunkGeneratedPayload(
                        message_chunk=text, metadata=chunk_metadata
                    ),
                )
            )
            state.add_message_chunk(text)

    async def _handle_message_stream_end(
        self,
        state: ConversationStreamState,
        on_event: Callable[[ConversationStreamEvent], Awaitable[None]],
    ):
        await on_event(
            ConversationStreamEvent(
                event="text_message_completed",
                payload=TextMessageCompletedPayload(full_message=state.get_full_response()),
            )
        )
        state.end_message_stream()

    async def _handle_custom_event(
        self,
        data: Dict[str, Any],
        state: ConversationStreamState,
        on_event: Callable[[ConversationStreamEvent], Awaitable[None]],
    ):
        logger.debug(
            f"Handling custom event: {data['event']}, message_stream_started: {state.has_message_stream_started()}"
        )

        if state.has_message_stream_started():
            logger.debug("Completing message stream due to custom event")
            await on_event(
                ConversationStreamEvent(
                    event="text_message_completed",
                    payload=TextMessageCompletedPayload(full_message=state.get_full_response()),
                )
            )
            state.end_message_stream()

        if data["event"] == "recipe_generation_started":
            state.start_recipe_generation()
            await on_event(
                ConversationStreamEvent(
                    event="recipe_generation_started",
                    payload=RecipeGenerationStartedPayload(
                        tool_name=data["tool_name"], tool_input=data["tool_input"]
                    ),
                )
            )

        elif data["event"] == "summary_updated":
            await on_event(
                ConversationStreamEvent(
                    event="summary_updated", payload=SummaryUpdatedPayload(summary=data["summary"])
                )
            )

        elif data["event"] == "thread_title_updated":
            await on_event(
                ConversationStreamEvent(
                    event="thread_title_updated",
                    payload=ThreadTitleUpdatedPayload(thread_title=data["thread_title"]),
                )
            )

        elif data["event"] == "search_started":
            await on_event(
                ConversationStreamEvent(
                    event="search_started",
                    payload=SearchStartedPayload(
                        tool_name=data["tool_name"], tool_input=data["tool_input"]
                    ),
                )
            )
            state.start_search()

        else:
            logger.error(f"Unexpected custom event: {data['event']}")

    async def _handle_error(
        self,
        error: Exception,
        state: ConversationStreamState,
        on_event: Callable[[ConversationStreamEvent], Awaitable[None]],
    ):
        logger.error(f"Error in stream_conversation: {str(error)}")
        await on_event(
            ConversationStreamEvent(
                event="ai_agent_error", payload=AIAgentErrorPayload(error_message=str(error))
            )
        )
        state.reset()

    def _should_ignore_ai_text_message_chunk(self, metadata: Dict[str, Any]) -> bool:
        langgraph_node = metadata.get("langgraph_node")
        if langgraph_node and langgraph_node in ["update_thread_title", "summarize_conversation"]:
            return True
        return False

    async def stream_conversation(
        self,
        user_id: str,
        thread_id: str,
        user_input: str,
        *,
        on_event: Callable[[ConversationStreamEvent], Awaitable[None]],
    ):
        logger.info(f"Starting conversation stream for user {user_id}, thread {thread_id}")

        config = self.get_agent_config(user_id, thread_id)

        agent = AgentFactory(
            user_id=user_id,
            thread_id=thread_id,
            checkpointer=self.checkpointer,
        ).build()

        state = ConversationStreamState()

        recipe_parser = StreamingRecipeFieldParser()

        try:
            input_state = {"messages": [HumanMessage(content=user_input)]}

            async for event, data in agent.astream(
                input_state, config, stream_mode=["messages", "custom"]
            ):
                logger.debug(f"Received event: {event}, data type: {type(data)}")

                if event == "messages" and isinstance(data, tuple):
                    chunk = data[0]
                    metadata = data[1]
                    logger.debug(f"Processing message chunk: {type(chunk)}, metadata: {metadata}")

                    if isinstance(chunk, ToolMessage) and chunk.status == "success":
                        await self._handle_tool_message(
                            chunk, metadata, recipe_parser, state, on_event
                        )
                        continue

                    if not isinstance(chunk, AIMessageChunk):
                        continue

                    if self._should_ignore_ai_text_message_chunk(metadata):
                        logger.debug(
                            f"Ignoring AI chunk from node: {metadata.get('langgraph_node')}"
                        )
                        continue

                    if (
                        not state.has_recipe_generation_started()
                        and not state.has_message_stream_started()
                    ):
                        # TODO: Distinguish between the recipe xml chunks and the text message chunks
                        await self._handle_ai_message_start(state, on_event)

                    await self._handle_ai_message_chunk(
                        chunk, metadata, state, recipe_parser, on_event
                    )

                elif event == "custom" and isinstance(data, dict) and "event" in data:
                    await self._handle_custom_event(data, state, on_event)

                else:
                    logger.error(f"Unexpected event: {event}")

            logger.debug("Agent stream completed, checking if message stream needs to be ended")
            if state.has_message_stream_started():
                await self._handle_message_stream_end(state, on_event)

        except Exception as e:
            await self._handle_error(e, state, on_event)
