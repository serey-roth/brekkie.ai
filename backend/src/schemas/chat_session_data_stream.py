from enum import Enum
from typing import Union

from pydantic import BaseModel, field_validator


class SyncCachedThreadWithDbEntry(BaseModel):
    user_id: str
    thread_id: str

class SyncCachedMessageWithDbEntry(BaseModel):
    user_id: str
    thread_id: str
    message_id: str

class SyncCachedRecipeWithDbEntry(BaseModel):
    user_id: str
    thread_id: str
    recipe_id: str
    
class ChatSessionStreamEntryType(Enum):
    SYNC_CACHED_THREAD_WITH_DB = "sync_cached_thread_with_db"
    SYNC_CACHED_MESSAGE_WITH_DB = "sync_cached_message_with_db"
    SYNC_CACHED_RECIPE_WITH_DB = "sync_cached_recipe_with_db"

class ChatSessionDataStreamEntry(BaseModel):
    type: ChatSessionStreamEntryType
    payload: Union[
        SyncCachedThreadWithDbEntry, 
        SyncCachedMessageWithDbEntry, 
        SyncCachedRecipeWithDbEntry, 
    ]
    
    @field_validator("payload")
    @classmethod
    def validate_payload(cls, v, info):
        type_value = info.data["type"]
        if type_value == ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB:
            if not isinstance(v, SyncCachedThreadWithDbEntry):
                raise ValueError(f"Invalid payload for type: {type_value}")
            return v
        elif type_value == ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB:
            if not isinstance(v, SyncCachedMessageWithDbEntry):
                raise ValueError(f"Invalid payload for type: {type_value}")
            return v
        elif type_value == ChatSessionStreamEntryType.SYNC_CACHED_RECIPE_WITH_DB:
            if not isinstance(v, SyncCachedRecipeWithDbEntry):
                raise ValueError(f"Invalid payload for type: {type_value}")
            return v
        else:
            raise ValueError(f"Invalid payload for type: {type_value}")
