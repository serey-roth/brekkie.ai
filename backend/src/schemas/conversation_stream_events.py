from pydantic import BaseModel, field_validator, Field
from typing import Literal

from schemas.recipes import Recipe, RecipeField


class ConversationStreamMetadata(BaseModel):
    model_name: str = Field(default="unknown")
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)


class TextMessageStartedPayload(BaseModel):
    pass


class TextMessageChunkGeneratedPayload(BaseModel):
    message_chunk: str
    metadata: ConversationStreamMetadata


class TextMessageCompletedPayload(BaseModel):
    full_message: str


class SearchStartedPayload(BaseModel):
    tool_name: str
    tool_input: dict


class SearchCompletedPayload(BaseModel):
    tool_output: dict
    tool_metadata: ConversationStreamMetadata


class RecipeGenerationStartedPayload(BaseModel):
    tool_name: str
    tool_input: dict


class RecipeFieldDetectedPayload(BaseModel):
    field: RecipeField


class RecipeGenerationCompletedPayload(BaseModel):
    recipe: Recipe
    tool_output: dict
    tool_metadata: ConversationStreamMetadata


class AIAgentErrorPayload(BaseModel):
    error_message: str


class SummaryUpdatedPayload(BaseModel):
    summary: str


class ThreadTitleUpdatedPayload(BaseModel):
    thread_title: str


class UserMessageRejectedPayload(BaseModel):
    rejection_message: str


# TODO: Replace with enum?
ConversationStreamEventName = Literal[
    "text_message_started",
    "text_message_chunk_generated",
    "text_message_completed",
    "search_started",
    "search_completed",
    "recipe_generation_started",
    "recipe_field_detected",
    "recipe_generation_completed",
    "ai_agent_error",
    "summary_updated",
    "thread_title_updated",
    "user_message_rejected",
]


class ConversationStreamEvent(BaseModel):
    event: ConversationStreamEventName
    payload: (
        TextMessageStartedPayload
        | TextMessageChunkGeneratedPayload
        | TextMessageCompletedPayload
        | SearchStartedPayload
        | SearchCompletedPayload
        | RecipeGenerationStartedPayload
        | RecipeFieldDetectedPayload
        | RecipeGenerationCompletedPayload
        | AIAgentErrorPayload
        | SummaryUpdatedPayload
        | ThreadTitleUpdatedPayload
        | UserMessageRejectedPayload
    )

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, v, info):
        event = info.data.get("event")
        if event == "text_message_started":
            if not isinstance(v, TextMessageStartedPayload):
                raise ValueError("text_message_started event should have TextMessageStartedPayload")
        elif event == "text_message_chunk_generated":
            if not isinstance(v, TextMessageChunkGeneratedPayload):
                raise ValueError(
                    "text_message_chunk_generated event should have TextMessageChunkGeneratedPayload"
                )
        elif event == "text_message_completed":
            if not isinstance(v, TextMessageCompletedPayload):
                raise ValueError(
                    "text_message_completed event should have TextMessageCompletedPayload"
                )
        elif event == "search_started":
            if not isinstance(v, SearchStartedPayload):
                raise ValueError("search_started event should have SearchStartedPayload")
        elif event == "search_completed":
            if not isinstance(v, SearchCompletedPayload):
                raise ValueError("search_completed event should have SearchCompletedPayload")
        elif event == "recipe_generation_started":
            if not isinstance(v, RecipeGenerationStartedPayload):
                raise ValueError(
                    "recipe_generation_started event should have RecipeGenerationStartedPayload"
                )
        elif event == "recipe_field_detected":
            if not isinstance(v, RecipeFieldDetectedPayload):
                raise ValueError(
                    "recipe_field_detected event should have RecipeFieldDetectedPayload"
                )
        elif event == "recipe_generation_completed":
            if not isinstance(v, RecipeGenerationCompletedPayload):
                raise ValueError(
                    "recipe_generation_completed event should have RecipeGenerationCompletedPayload"
                )
        elif event == "ai_agent_error":
            if not isinstance(v, AIAgentErrorPayload):
                raise ValueError("ai_agent_error event should have AIAgentErrorPayload")
        elif event == "summary_updated":
            if not isinstance(v, SummaryUpdatedPayload):
                raise ValueError("summary_updated event should have SummaryUpdatedPayload")
        elif event == "thread_title_updated":
            if not isinstance(v, ThreadTitleUpdatedPayload):
                raise ValueError("thread_title_updated event should have ThreadTitleUpdatedPayload")
        elif event == "user_message_rejected":
            if not isinstance(v, UserMessageRejectedPayload):
                raise ValueError(
                    "user_message_rejected event should have UserMessageRejectedPayload"
                )
        return v
