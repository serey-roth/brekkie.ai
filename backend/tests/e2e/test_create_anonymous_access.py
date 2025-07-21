from datetime import datetime, timezone

import pytest

from fastapi import status

from services.service_container import ServiceContainer

from utils.date_utils import to_utc_isostring


class TestCreateAnonymousAccess:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_successful_create_anonymous_access(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.1"
        
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        user_access = await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access.access_token,
            user_id=user_access.user_id,
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            user_message_count=5,
        )

        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)

        response = await async_client.post("/api/access/create-anonymous-access", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["access_token"] != user_access.access_token
        assert response_data["user_id"] != user_access.user_id  # New anonymous session gets new user_id
        assert response_data["is_authenticated"] is False
        assert response_data["user_message_count"] == 0
        assert response_data["created_at"] is not None
        assert response_data["updated_at"] is not None
        
        new_cookie = response.cookies.get("bk_access_token")
        assert new_cookie is not None
        assert new_cookie == response_data["access_token"]

        old_token_exists = await service_container.user_access_cache_service.get_user_access(user_access.access_token)
        assert old_token_exists is None

        new_token_exists = await service_container.user_access_cache_service.get_user_access(response_data["access_token"])
        assert new_token_exists is not None
        assert new_token_exists.access_token == response_data["access_token"]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_access_token(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.2"
        
        headers = {
            "fly-client-ip": sample_ip_address
        }

        response = await async_client.post("/api/access/create-anonymous-access", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Missing access token"

    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_access_token(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.3"
        
        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", "invalid_token")

        response = await async_client.post("/api/access/create-anonymous-access", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Access token not found"

    @pytest.mark.asyncio(loop_scope="session")
    async def test_create_anonymous_access_clears_rate_limiter(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.5"
        
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        user_access = await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access.access_token,
            user_id=user_access.user_id,
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            user_message_count=3,
        )

        await service_container.anonymous_access_service.ip_rate_limiter.increment_anonymous_access_count(sample_ip_address)

        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)

        response = await async_client.post("/api/access/create-anonymous-access", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        
        rate_limit_count = await service_container.anonymous_access_service.ip_rate_limiter.get_current_anonymous_access_count(sample_ip_address)
        assert rate_limit_count == 0

    @pytest.mark.asyncio(loop_scope="session")
    async def test_new_token_has_fresh_ttl(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.6"
        
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        user_access = await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access.access_token,
            user_id=user_access.user_id,
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            user_message_count=10,
        )

        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)

        response = await async_client.post("/api/access/create-anonymous-access", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        new_token_ttl = await service_container.user_access_cache_service.get_ttl(response_data["access_token"])
        assert new_token_ttl is not None
        assert new_token_ttl > 0

    @pytest.mark.asyncio(loop_scope="session")
    async def test_create_anonymous_access_creates_new_user_id(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.7"
        
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        original_user_id = user_access.user_id
        
        user_access = await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access.access_token,
            user_id=user_access.user_id,
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            user_message_count=7,
        )

        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)

        response = await async_client.post("/api/access/create-anonymous-access", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["user_id"] != original_user_id  # Creates new anonymous session with new user_id
        