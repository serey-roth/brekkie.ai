from datetime import datetime, timezone

import pytest

from fastapi import status

from src.services.service_container import ServiceContainer

from src.utils.date_utils import to_utc_isostring


class TestRevokeAccess:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_successful_revoke(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.1"
        
        user_access = await service_container.user_access_cache_service.create_user_access(
            access_token="test-token-123",
            user_id="test-user-123",
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            is_authenticated=True,
            user_message_count=5,
            ip_address=sample_ip_address
        )

        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)

        response = await async_client.post("/api/access/revoke-access", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        
        old_user_access = await service_container.user_access_cache_service.get_user_access(user_access.access_token)
        assert old_user_access is None

        cookie_value = response.cookies.get("bk_access_token")
        assert cookie_value is None or cookie_value == ""

    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_access_token(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.2"
        
        headers = {
            "fly-client-ip": sample_ip_address
        }

        response = await async_client.post("/api/access/revoke-access", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Missing access token"

    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_access_token(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.3"
        
        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", "invalid_token")

        response = await async_client.post("/api/access/revoke-access", headers=headers)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio(loop_scope="session")
    async def test_revoke_clears_cookie(self, async_client, service_container: ServiceContainer):
        sample_ip_address = "127.0.0.8"
        
        user_access = await service_container.user_access_cache_service.create_user_access(
            access_token="cookie-token-123",
            user_id="cookie-user-123",
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            is_authenticated=True,
            user_message_count=7,
            ip_address=sample_ip_address
        )

        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)

        response = await async_client.post("/api/access/revoke-access", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        
        cookie_value = response.cookies.get("bk_access_token")
        assert cookie_value is None or cookie_value == "" 
        