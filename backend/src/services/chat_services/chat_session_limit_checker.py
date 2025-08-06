from schemas.chat_session_errors import AccessTokenNotFoundError
from services.data_services.user_access_cache_service import UserAccessCacheService


class ChatSessionLimitChecker:
    def __init__(
        self,
        authenticated_user_message_limit: int,
        unauthenticated_user_message_limit: int,
        user_access_cache_service: UserAccessCacheService,
    ):
        self.authenticated_user_message_limit = authenticated_user_message_limit
        self.unauthenticated_user_message_limit = unauthenticated_user_message_limit
        self.user_access_cache_service = user_access_cache_service

    async def has_message_limit_reached(self, access_token: str) -> bool:
        user_access = await self.user_access_cache_service.get_user_access(access_token)
        if user_access is None:
            raise AccessTokenNotFoundError(access_token=access_token)

        if user_access.is_authenticated:
            result = user_access.user_message_count >= self.authenticated_user_message_limit
        else:
            result = user_access.user_message_count >= self.unauthenticated_user_message_limit
        return bool(result)

    async def get_message_limit(self, access_token: str) -> int:
        user_access = await self.user_access_cache_service.get_user_access(access_token)
        if user_access is None:
            raise AccessTokenNotFoundError(access_token=access_token)

        if user_access.is_authenticated:
            return self.authenticated_user_message_limit
        else:
            return self.unauthenticated_user_message_limit
