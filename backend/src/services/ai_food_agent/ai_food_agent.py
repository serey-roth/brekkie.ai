from abc import ABC, abstractmethod
from typing import Callable, Awaitable

from langchain_core.messages import AIMessageChunk
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver

from schemas.conversation_stream_events import ConversationStreamEvent

from utils.logger import Logger

logger = Logger("ai_food_agent")


class AIFoodAgent(ABC):
    def __init__(self, checkpointer: BaseCheckpointSaver):
        self.checkpointer = checkpointer
        
        
    def get_agent_config(self, user_id: str, thread_id: str):
        return RunnableConfig(configurable={"user_id": user_id, "thread_id": thread_id}, tags=["food_agent"], metadata={"thread_id": thread_id})
    
    
    def update_memory(self, messages: list, user_id: str, thread_id: str):
        # Memory updates disabled for now - can be re-enabled later
        # config = self.get_agent_config(user_id, thread_id)
        # user_profile_memory.update_user_profile_memory_delayed(messages, config, self.store, user_id)
        pass
    
    
    def extract_text_from_chunk(self, chunk: AIMessageChunk) -> str:
        if isinstance(chunk.content, str):
            return chunk.content
        else:
            result = "".join(
                str(item) if isinstance(item, (int, float))
                else item if isinstance(item, str)  
                else item.get("text", "") if isinstance(item, dict)
                else str(item)
                for item in chunk.content
            )
            return result


    @abstractmethod
    async def stream_conversation(
        self, 
        user_id: str, 
        thread_id: str, 
        user_input: str, 
        *, 
        on_event: Callable[[ConversationStreamEvent], Awaitable[None]],
    ):
        pass
