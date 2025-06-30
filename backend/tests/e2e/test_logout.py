import pytest
from fastapi import status

from src.services.service_container import ServiceContainer
from tests.utils.assert_deep_equal import assert_deep_equal


class TestLogout:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_successful_logout(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access_data.access_token,
            user_id=user_access_data.user_id,
            email="test@example.com",
            name="Test User",
        )
        
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_authenticated"] is False
        
        assert await service_container.user_access_cache_service.get_user_access(user_access_data.access_token) is None

    @pytest.mark.asyncio(loop_scope="session")
    async def test_not_authenticated_user(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()

        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert_deep_equal(response.json(), {"detail": {"message": "User not authenticated"}})

    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_token(self, async_client, service_container: ServiceContainer):
        response = await async_client.post("/api/auth/logout")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})
        
        headers = {}
        response = await async_client.post("/api/auth/logout", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})
        
        headers = {"Authorization": "Access "}
        response = await async_client.post("/api/auth/logout", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})
        
        headers = {"Authorization": "Bearer "}
        response = await async_client.post("/api/auth/logout", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_token(self, async_client, service_container: ServiceContainer):
        headers = {"Authorization": f"Bearer invalid_token"}

        response = await async_client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Access token is invalid or expired"}})