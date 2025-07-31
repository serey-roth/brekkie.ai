from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from fastapi import status

from services.service_container import ServiceContainer

from utils.date_utils import to_utc_isostring


class TestEnsureAccess:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_valid_token(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.1"
        
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)

        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)

        response = await async_client.post("/api/access/ensure-access", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] == user_access.access_token
        assert response.json()["user_id"] == user_access.user_id
        assert response.json()["is_authenticated"] is False
        assert response.json()["user_message_count"] == 0
        assert response.json()["created_at"] is not None
        assert response.json()["updated_at"] is not None
        assert response.json()["ip_address"] == sample_ip_address

        assert response.cookies.get("bk_access_token") is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_authenticated_token(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.2"
        
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        user_access = await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access.access_token,
            user_id=user_access.user_id,
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            user_message_count=0,
        )

        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)

        response = await async_client.post("/api/access/ensure-access", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] == user_access.access_token
        assert response.json()["user_id"] == user_access.user_id
        assert response.json()["is_authenticated"] is True
        assert response.json()["user_message_count"] == 0
        assert response.json()["created_at"] is not None
        assert response.json()["updated_at"] is not None
        assert response.json()["ip_address"] == sample_ip_address
        
        assert response.cookies.get("bk_access_token") is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_no_token(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.3"
        
        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        response = await async_client.post("/api/access/ensure-access", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Missing access token"
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_token(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.4"
        
        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", "invalid_token")
        
        response = await async_client.post("/api/access/ensure-access", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Access record not found"
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_expired_token(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.5"
        
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)

        await service_container.user_access_cache_service.revoke_access(user_access.access_token)

        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)

        response = await async_client.post("/api/access/ensure-access", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Access record not found"
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_almost_expired_token(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.6"
        
        with patch.object(service_container.user_access_cache_service, 'get_ttl', return_value=10):
            user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)

            exist = await service_container.user_access_cache_service.get_user_access(user_access.access_token)
            assert exist is not None
            assert exist.access_token == user_access.access_token
            
            headers = {
                "fly-client-ip": sample_ip_address
            }
            
            async_client.cookies.set("bk_access_token", user_access.access_token)

            response = await async_client.post("/api/access/ensure-access", headers=headers)

            assert response.status_code == status.HTTP_200_OK
            assert response.json()["access_token"] != user_access.access_token
            assert response.json()["user_id"] == user_access.user_id
            assert response.json()["is_authenticated"] is False
            assert response.json()["user_message_count"] == 0
            assert response.json()["created_at"] is not None
            assert response.json()["updated_at"] is not None
            assert response.json()["ip_address"] == sample_ip_address
            
            assert response.cookies.get("bk_access_token") is not None
            
            old_user_access = await service_container.user_access_cache_service.get_user_access(user_access.access_token)
            assert old_user_access is None
