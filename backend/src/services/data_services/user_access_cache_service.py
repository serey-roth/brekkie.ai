from datetime import datetime, timezone
from uuid import uuid4

from services.redis.redis_client import RedisClient
from services.redis.redis_cache import RedisCache

from schemas.user_access import UserAccessData

from utils.date_utils import to_utc_isostring


class UserAccessCacheService:
    def __init__(self, redis_client: RedisClient, ttl: int): 
        self.redis_cache = RedisCache[UserAccessData](redis_client)
        self.ttl = ttl

    
    def _get_user_access_key(self, access_token: str) -> str:
        return f"brekkie:user_access:{access_token}"


    async def get_user_access(self, access_token: str) -> UserAccessData | None:
        return await self.redis_cache.get_json(self._get_user_access_key(access_token), UserAccessData)
    

    async def set_user_access(self, access_token: str, data: UserAccessData, ttl: int | None = None, keep_ttl: bool = False) -> UserAccessData:
        if keep_ttl:
            set_ttl = None
        else:
            set_ttl = ttl if ttl is not None else self.ttl
        await self.redis_cache.set_json(self._get_user_access_key(access_token), data.model_dump(mode="json"), ttl=set_ttl, keep_ttl=keep_ttl)
        return data
    
    
    async def create_user_access(self, access_token: str, user_id: str, *, name: str | None = None, email: str | None = None, is_authenticated: bool = False, user_message_count: int = 0, created_at: str | None = None, updated_at: str | None = None, ip_address: str | None = None, ttl: int | None = None) -> UserAccessData:
        return await self.set_user_access(access_token, UserAccessData(
            access_token=access_token,
            user_id=user_id,
            name=name,
            email=email,
            is_authenticated=is_authenticated,
            user_message_count=user_message_count,
            created_at=created_at,
            updated_at=updated_at,
            ip_address=ip_address,
        ), ttl=ttl)
    
    
    async def create_anonymous_access(self, ip_address: str | None = None, ttl: int | None = None) -> UserAccessData:
        access_token = str(uuid4())
        user_id = str(uuid4())
        now = to_utc_isostring(datetime.now(timezone.utc))
        return await self.create_user_access(access_token, user_id, is_authenticated=False, created_at=now, updated_at=now, ip_address=ip_address, ttl=ttl)
    
    
    async def promote_to_authenticated(self, access_token: str, user_id: str, email: str, name: str, updated_at: str, user_message_count: int, ttl: int | None = None) -> UserAccessData:
        user_access = await self.get_user_access(access_token)
        if user_access is None:
            raise ValueError(f"User access {access_token} not found")
        
        user_access = user_access.model_copy(update={"user_id": user_id, "email": email, "name": name, "is_authenticated": True, "user_message_count": user_message_count, "updated_at": updated_at}, deep=True)
        user_access = await self.set_user_access(access_token, user_access, ttl=ttl)
        return user_access
    
    
    async def increment_user_message_count(self, access_token: str) -> UserAccessData:
        user_access = await self.get_user_access(access_token)
        if user_access is None:
            raise ValueError(f"User access {access_token} not found")
        
        user_access = user_access.model_copy(update={"user_message_count": user_access.user_message_count + 1}, deep=True)
        user_access = await self.set_user_access(access_token, user_access, keep_ttl=True)
        return user_access

    
    async def is_authenticated(self, access_token: str) -> bool:
        user_access = await self.get_user_access(access_token)
        return user_access.is_authenticated if user_access else False

    
    async def is_expired(self, access_token: str) -> bool:
        return not await self.redis_cache.exists(self._get_user_access_key(access_token))
    

    async def revoke_access(self, access_token: str) -> None:
        await self.redis_cache.delete(self._get_user_access_key(access_token))
        
        
    async def get_ttl(self, access_token: str) -> int:
        return await self.redis_cache.get_ttl(self._get_user_access_key(access_token))
    