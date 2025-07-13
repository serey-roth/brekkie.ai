from datetime import datetime, timezone

import pytest

from fastapi import status

from config.settings import Settings

from services.service_container import ServiceContainer

from utils.date_utils import to_utc_isostring

from tests.test_helpers.assert_deep_equal import assert_deep_equal


class TestLogout:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_successful_logout(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access_data.access_token,
            user_id=user_access_data.user_id,
            email="test@example.com",
            name="Test User",
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            user_message_count=0,
        )
        
        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        
        old_user_access_data = await service_container.user_access_cache_service.get_user_access(user_access_data.access_token)
        assert old_user_access_data is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_not_authenticated_user(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)

        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_token(self, async_client, service_container: ServiceContainer):
        response = await async_client.post("/api/auth/logout")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.cookies.get("bk_access_token") is None
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_token(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        headers = {
            "fly-client-ip": sample_ip_address
        }

        async_client.cookies.set("bk_access_token", "invalid_token")
        response = await async_client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.cookies.get("bk_access_token") is None
        assert_deep_equal(response.json(), {"detail": {"message": "Access token not found"}})

    @pytest.mark.asyncio(loop_scope="session")
    async def test_logout_with_auth_disabled(self, async_client, service_container: ServiceContainer, test_settings: Settings):
        # TODO: This is a hack to override the settings for the test
        from api.main import app
        from api.deps import get_settings
        new_settings = test_settings.model_copy(update={"enable_auth": False})
        app.dependency_overrides[get_settings] = lambda: new_settings

        try:
            response = await async_client.post("/api/auth/logout", headers={})
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert_deep_equal(response.json(), {"detail": {"message": "Feature temporarily unavailable. Please check back later."}})
        
        finally:
            app.dependency_overrides = {}