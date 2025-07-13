# import os

# from typing import Annotated, Optional, cast
# from langmem import ReflectionExecutor, create_memory_store_manager
# from langgraph.store.base import BaseStore
# from pydantic import BaseModel, Field


# class UserProfile(BaseModel):
#     """Collection of information the user has shared about themselves"""
#     name: Annotated[Optional[str], Field(description="The user's name")] = None
#     user_age: Annotated[Optional[int], Field(description="The user's age")] = None
#     gender: Annotated[Optional[str], Field(description="The user's gender")] = None
#     location: Annotated[Optional[str], Field(description="The user's location")] = None
#     occupation: Annotated[Optional[str], Field(description="The user's occupation")] = None
#     interests: Annotated[Optional[list[str]], Field(description="The user's interests")] = None
#     food_relationship: Annotated[Optional[str], Field(description="The user's relationship to food and cooking")] = None
#     communication_style: Annotated[Optional[str], Field(description="The user's communication style")] = None


# user_profile_memory_manager = create_memory_store_manager(
#     "anthropic:claude-sonnet-4-20250514",
#     query_model="anthropic:claude-3-5-haiku-latest",
#     namespace=("brekkie", "{user_id}", "profile"),
#     schemas=[UserProfile],
#     enable_inserts=False,
#     instructions="""
#         <goal>
#             Update this document to maintain up-to-date information about the user based on what they've shared.
#         </goal>

#         <guidelines>
#             Keep entries factual, concise (1-2 short sentences), and limited to stated information.

#             Avoid:
#             - Psychological interpretation ("suggesting", "indicating", "representing")
#             - Emotional analysis beyond what they explicitly express
#             - Inferring motivations or deeper meanings
#             - Adding descriptive language they didn't use
#         </guidelines>

#         <food_relationship>
#             For food relationship, focus on how the user talks ABOUT food and cooking.
#             Observe:
#             - Core food attributes: dietary choices, allergies, cultural background, personal food values, and fundamental preferences that define how they relate to food
#             - Practical cooking situation: kitchen setup, equipment, time constraints, lifestyle factors, living situation, and environmental factors that affect their cooking
#             - Current cooking skills and confidence: what they can make, kitchen comfort level, techniques mastered, and self-assessed cooking proficiency
#             - Cooking and eating experiences: past patterns, current habits, recent changes, ongoing efforts, and what they're working toward
#         </food_relationship>

#         <communication_style>
#             For communication style, focus on how the user talks TO Milo and what Milo responses work best.
#             Observe:
#             - Their communication tone and style when talking to Milo
#             - What Milo responses get positive reactions from them
#             - How comfortable they seem with Milo's personality
#             - Any patterns in how they engage with Milo
#         </communication_style>

#     """
# )


# def update_user_profile_memory(messages: list, config: dict, store: BaseStore, delay: int = 10):
#     """Update the user's profile"""
#     reflection = ReflectionExecutor(user_profile_memory_manager, store=store)
#     reflection.submit({
#         "messages": messages,
#     }, after_seconds=delay, config=config)


# async def get_user_profile_memory(user_id: str, store: BaseStore) -> Optional[UserProfile]:
#     user_profile_results = await store.asearch(("brekkie", user_id, "profile"), query="the user profile", limit=1)
#     if user_profile_results and user_profile_results[0].value and "content" in user_profile_results[0].value and user_profile_results[0].value["content"] is not None and isinstance(user_profile_results[0].value["content"], dict):
#         content = user_profile_results[0].value["content"]
#         return UserProfile.model_validate(content)
#     else:
#         return None


# __all__ = ["update_user_profile_memory", "get_user_profile_memory"]
