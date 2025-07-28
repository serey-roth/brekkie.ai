import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
env_file = os.path.join(os.path.dirname(backend_dir), '.env.development')

from dotenv import load_dotenv

load_dotenv(env_file)

import asyncio
import uuid
from contextlib import asynccontextmanager

from config.settings import create_settings
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

settings = create_settings(".env.development")

from schemas.conversation_stream_events import (
    AIAgentErrorPayload,
    ConversationStreamEvent,
    RecipeFieldDetectedPayload,
    RecipeGenerationCompletedPayload,
    RecipeGenerationStartedPayload,
    SearchCompletedPayload,
    SearchStartedPayload,
    SummaryUpdatedPayload,
    TextMessageChunkGeneratedPayload,
    TextMessageCompletedPayload,
    TextMessageStartedPayload,
    ThreadTitleUpdatedPayload,
    UserMessageRejectedPayload,
)
from schemas.recipes import RecipeCategory, RecipeIngredient, RecipeInstruction
from services.ai_food_agent.google_ai_food_agent import GoogleAIFoodAgent


async def get_user_input() -> str:
    return input("\nYou: ")


async def handle_message_start(message_id: str, payload: TextMessageStartedPayload):
    print("\nMilo: ", end="", flush=True)


async def handle_message_chunk(message_id: str, payload: TextMessageChunkGeneratedPayload):
    print(payload.message_chunk, end="", flush=True)


async def handle_message_end(message_id: str, payload: TextMessageCompletedPayload):
    print()  # Just a newline to end the message


async def handle_recipe_start(message_id: str, payload: RecipeGenerationStartedPayload):
    print(f"\n\n🔍 Tool call args: {payload.tool_name} {payload.tool_input}")
    print("─────────────────────────────────────────────────────────")
    print("\n\n┌─────────────────────────────────────────────────────────┐")
    print("│ 🍳 Generating Recipe...                                 │")
    print("└─────────────────────────────────────────────────────────┘")


async def handle_recipe_field(message_id: str, payload: RecipeFieldDetectedPayload):
    field_name = payload.field.name
    field_value = payload.field.value

    if field_name == "name":
        print(f"\n📝 {field_value}")
        print("─" * len(str(field_value)) + "──")
    elif field_name == "description":
        print(f"   {field_value}")
    elif field_name == "prep_time_minutes":
        prep_time = field_value
        print(f"\n⏱️  Prep: {prep_time} min", end="")
    elif field_name == "cook_time_minutes":
        cook_time = field_value
        print(f" | Cook: {cook_time} min", end="")
    elif field_name == "servings":
        servings = field_value
        print(f" | Serves: {servings}\n")
    elif field_name == "ingredient":
        ingredient = RecipeIngredient.model_validate(field_value)
        print(f"\n🍴 Ingredient: {ingredient.name} ({ingredient.quantity} {ingredient.unit})")
    elif (
        field_name == "ingredients"
        and isinstance(field_value, list)
        and all(isinstance(item, RecipeIngredient) for item in field_value)
    ):
        print("\n🍴 Ingredients:")
        if isinstance(field_value, list):
            for ingredient_data in field_value:
                ingredient = RecipeIngredient.model_validate(ingredient_data)
                print(f"   • {ingredient.name} ({ingredient.quantity} {ingredient.unit})")
    elif field_name == "instruction":
        print("\n👨‍🍳 Instruction:")
        instruction = RecipeInstruction.model_validate(field_value)
        print(f"   {instruction.title} - {instruction.description}")
    elif (
        field_name == "instructions"
        and isinstance(field_value, list)
        and all(isinstance(item, RecipeInstruction) for item in field_value)
    ):
        print("\n👨‍🍳 Instructions:")
        if isinstance(field_value, list):
            for instruction_data in field_value:
                instruction = RecipeInstruction.model_validate(instruction_data)
                print(f"   • {instruction.title} - {instruction.description}")
    elif field_name == "category":
        category = RecipeCategory.model_validate(field_value)
        print(f"\n🏷️  Category: {category.name}")
    elif (
        field_name == "categories"
        and isinstance(field_value, list)
        and all(isinstance(item, RecipeCategory) for item in field_value)
    ):
        print("\n🏷️  Categories:")
        if isinstance(field_value, list):
            for category_data in field_value:
                category = RecipeCategory.model_validate(category_data)
                print(f"   • {category.name}")
    elif field_name == "chef_notes":
        print("\n💡 Chef's Notes:")
        print(f"   {field_value}")
    elif field_name == "substitutions":
        print("\n🔄 Substitutions:")
        print(f"   {field_value}")
    elif field_name == "make_ahead_tips":
        print("\n⏰ Make Ahead Tips:")
        print(f"   {field_value}")
    elif field_name == "equipment_alternatives":
        print("\n🔧 Equipment Alternatives:")
        print(f"   {field_value}")
    elif field_name == "coordination_timeline":
        print("\n📅 Coordination Timeline:")
        print(f"   {field_value}")
    elif field_name == "scaling_guidance":
        print("\n📊 Scaling Guidance:")
        print(f"   {field_value}")
    elif field_name == "storage_notes":
        print("\n🗄️  Storage Notes:")
        print(f"   {field_value}")
    elif field_name == "serving_suggestions":
        print("\n🍽️  Serving Suggestions:")
        print(f"   {field_value}")


async def handle_recipe_complete(message_id: str, payload: RecipeGenerationCompletedPayload):
    print(f"\n\n✅ Recipe completed with metadata: {payload.tool_metadata.model_dump()}")
    print("─" * 60)


async def handle_search_started(message_id: str, payload: SearchStartedPayload):
    print(f"\n\n🔍 Search Started: {payload.tool_name} {payload.tool_input}")


async def handle_search_completed(message_id: str, payload: SearchCompletedPayload):
    print(f"\n\n🔍 Search Completed: {payload.tool_output} {payload.tool_metadata.model_dump()}")


async def handle_ai_agent_error(payload: AIAgentErrorPayload):
    print(f"\n❌ An error occurred: {payload.error_message}")


async def handle_summary_updated(payload: SummaryUpdatedPayload):
    print(f"\n\n💬 Summary: {payload.summary}")


async def handle_thread_title_updated(payload: ThreadTitleUpdatedPayload):
    print(f"\n\n💬 Thread Title: {payload.thread_title}")


async def handle_user_message_rejected(payload: UserMessageRejectedPayload):
    print(f"\n\n{payload.rejection_message}")


@asynccontextmanager
async def test_setup():
    checkpointer = InMemorySaver()
    yield checkpointer


@asynccontextmanager
async def prod_setup():
    checkpoint_db_url = settings.checkpoint_db_url
    if not checkpoint_db_url:
        raise ValueError("CHECKPOINT_DB_URL environment variable is required")

    async with (
        AsyncPostgresSaver.from_conn_string(checkpoint_db_url) as checkpointer,
    ):
        await checkpointer.setup()
        yield checkpointer


async def main():
    user_id = "user_123"
    thread_id = "thread_123"

    async with test_setup() as checkpointer:
        ai_agent_service = GoogleAIFoodAgent(
            checkpointer=checkpointer,
        )

        assistant_message_id = None

        async def on_event(event: ConversationStreamEvent):
            nonlocal assistant_message_id
            match event.event:
                case "text_message_started":
                    if isinstance(event.payload, TextMessageStartedPayload):
                        assistant_message_id = str(uuid.uuid4())
                        await handle_message_start(assistant_message_id, event.payload)
                case "text_message_chunk_generated":
                    if assistant_message_id is not None and isinstance(
                        event.payload, TextMessageChunkGeneratedPayload
                    ):
                        await handle_message_chunk(assistant_message_id, event.payload)
                case "text_message_completed":
                    if assistant_message_id is not None and isinstance(
                        event.payload, TextMessageCompletedPayload
                    ):
                        await handle_message_end(assistant_message_id, event.payload)
                    assistant_message_id = None
                case "recipe_generation_started":
                    if isinstance(event.payload, RecipeGenerationStartedPayload):
                        assistant_message_id = str(uuid.uuid4())
                        await handle_recipe_start(assistant_message_id, event.payload)
                case "recipe_field_detected":
                    if assistant_message_id is not None and isinstance(
                        event.payload, RecipeFieldDetectedPayload
                    ):
                        await handle_recipe_field(assistant_message_id, event.payload)
                case "recipe_generation_completed":
                    if assistant_message_id is not None and isinstance(
                        event.payload, RecipeGenerationCompletedPayload
                    ):
                        await handle_recipe_complete(assistant_message_id, event.payload)
                        assistant_message_id = None
                case "search_started":
                    if isinstance(event.payload, SearchStartedPayload):
                        assistant_message_id = str(uuid.uuid4())
                        await handle_search_started(assistant_message_id, event.payload)
                case "search_completed":
                    if assistant_message_id is not None and isinstance(
                        event.payload, SearchCompletedPayload
                    ):
                        await handle_search_completed(assistant_message_id, event.payload)
                    assistant_message_id = None
                case "summary_updated":
                    if isinstance(event.payload, SummaryUpdatedPayload):
                        await handle_summary_updated(event.payload)
                case "thread_title_updated":
                    if isinstance(event.payload, ThreadTitleUpdatedPayload):
                        await handle_thread_title_updated(event.payload)
                case "ai_agent_error":
                    if isinstance(event.payload, AIAgentErrorPayload):
                        await handle_ai_agent_error(event.payload)
                    assistant_message_id = None
                case "user_message_rejected":
                    if isinstance(event.payload, UserMessageRejectedPayload):
                        await handle_user_message_rejected(event.payload)
                case _:
                    print(f"Unhandled event: {event.event}")

    while True:
        user_input = await get_user_input()
        if user_input.lower() == "quit":
            break

        await ai_agent_service.stream_conversation(
            user_id=user_id,
            thread_id=thread_id,
            user_input=user_input,
            on_event=on_event,
        )


if __name__ == "__main__":
    asyncio.run(main())
