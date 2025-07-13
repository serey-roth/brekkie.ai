# from langgraph.store.base import BaseStore

# from ai.memory.user_profile import UserProfile, update_user_profile_memory


# class ChatSessionMemoryManager:
#     def __init__(self, store: BaseStore):
#         self.store = store

#     async def get_user_profile(self, user_id: str, thread_id: str):
#         user_profile_results = await self.store.asearch(
#             ("brekkie", user_id, "profile"), query="the user profile", limit=1
#         )
#         if (
#             user_profile_results
#             and user_profile_results[0].value
#             and "content" in user_profile_results[0].value
#             and user_profile_results[0].value["content"] is not None
#             and isinstance(user_profile_results[0].value["content"], dict)
#         ):
#             content = user_profile_results[0].value["content"]
#             return UserProfile.model_validate(content)
#         else:
#             return None

#     def update_user_profile_delayed(
#         self, user_id: str, thread_id: str, user_message: str, delay: int = 10
#     ):
#         update_user_profile_memory(
#             messages=[{"role": "user", "content": user_message}],
#             config={"user_id": user_id, "thread_id": thread_id},
#             store=self.store,
#             delay=delay,
#         )
