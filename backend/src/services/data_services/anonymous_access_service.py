from schemas.api_error import RateLimitError
from schemas.user_access import UserAccessData

from services.data_services.user_access_cache_service import UserAccessCacheService
from services.data_services.anonymous_access_rate_limiter import AnonymousAccessIpAddressRateLimiter

class AnonymousAccessService:
    def __init__(
        self, 
        user_access_cache_service: UserAccessCacheService,
        ip_rate_limiter: AnonymousAccessIpAddressRateLimiter,
    ):
        self.user_access_cache_service = user_access_cache_service
        self.ip_rate_limiter = ip_rate_limiter
        
    async def get_or_create_user_access(self, ip_address: str, access_token: str | None = None) -> UserAccessData:
        if access_token:
            user_access = await self.user_access_cache_service.get_user_access(access_token)
            if user_access is not None:
                return user_access
        
        is_rate_limited = await self.ip_rate_limiter.is_rate_limited(ip_address)
        if is_rate_limited:
            raise RateLimitError(ip_address)
        
        await self.ip_rate_limiter.increment(ip_address)
        
        return await self.user_access_cache_service.create_anonymous_access()
