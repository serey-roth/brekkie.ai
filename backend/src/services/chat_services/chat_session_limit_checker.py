from services.data_services.user_access_cache_service import UserAccessCacheService

from schemas.chat_session_errors import AccessTokenNotFoundError

class ChatSessionLimitChecker:
    def __init__(
        self, 
        authenticated_user_message_limit: int, 
        unauthenticated_user_message_limit: int, 
        user_access_cache_service: UserAccessCacheService
    ):
        self.authenticated_user_message_limit = authenticated_user_message_limit
        self.unauthenticated_user_message_limit = unauthenticated_user_message_limit
        self.user_access_cache_service = user_access_cache_service
        
        
    async def has_message_limit_reached(self, access_token: str) -> bool:
        user_access_data = await self.user_access_cache_service.get_user_access(access_token)
        if user_access_data is None:
            raise AccessTokenNotFoundError(access_token=access_token)
        
        if user_access_data.is_authenticated:
            return user_access_data.user_message_count >= self.authenticated_user_message_limit
        else:
            return user_access_data.user_message_count >= self.unauthenticated_user_message_limit
        
    
    async def get_message_limit(self, access_token: str) -> int:
        user_access_data = await self.user_access_cache_service.get_user_access(access_token)
        if user_access_data is None:
            raise AccessTokenNotFoundError(access_token=access_token)
        
        if user_access_data.is_authenticated:
            return self.authenticated_user_message_limit
        else:
            return self.unauthenticated_user_message_limit