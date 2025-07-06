from datetime import datetime, timezone

import pytest

from fastapi import status

from services.service_container import ServiceContainer

from utils.date_utils import to_utc_isostring

from tests.test_helpers.assert_deep_equal import assert_deep_equal


class TestLogout:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_successful_logout(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access_data.access_token,
            user_id=user_access_data.user_id,
            email="test@example.com",
            name="Test User",
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            user_message_count=0,
        )
        
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.cookies.get("bk_access_token") is not None
        assert response.json()["is_authenticated"] is False
        
        old_user_access_data = await service_container.user_access_cache_service.get_user_access(user_access_data.access_token)
        assert old_user_access_data is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_not_authenticated_user(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()

        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.cookies.get("bk_access_token") is None
        assert_deep_equal(response.json(), {"detail": {"message": "User not authenticated"}})

    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_token(self, async_client, service_container: ServiceContainer):
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        response = await async_client.post("/api/auth/logout", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.cookies.get("bk_access_token") is None
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_token(self, async_client, service_container: ServiceContainer):
        headers = {
            "fly-client-ip": "192.168.1.100"
        }

        async_client.cookies.set("bk_access_token", "invalid_token")
        response = await async_client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.cookies.get("bk_access_token") is None
        assert_deep_equal(response.json(), {"detail": {"message": "Access token not found"}})
