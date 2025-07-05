import pytest

from fastapi import status

from src.services.service_container import ServiceContainer


class TestEnsureAccessToken:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_valid_token(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()

        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/access-token/ensure-access-token", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] == user_access_data.access_token
        assert response.json()["user_id"] == user_access_data.user_id
        assert response.json()["email"] == user_access_data.email
        assert response.json()["name"] == user_access_data.name
        assert response.json()["is_authenticated"] is False
        assert response.json()["user_message_count"] == 0
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_authenticated_token(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        user_access_data = await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access_data.access_token,
            user_id=user_access_data.user_id,
            email="test@example.com",
            name="Test User",
        )

        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/access-token/ensure-access-token", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] == user_access_data.access_token
        assert response.json()["user_id"] == user_access_data.user_id
        assert response.json()["email"] == user_access_data.email
        assert response.json()["name"] == user_access_data.name
        assert response.json()["is_authenticated"] is True
        assert response.json()["user_message_count"] == 0
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_expired_token(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()

        await service_container.user_access_cache_service.revoke_access(user_access_data.access_token)

        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/access-token/ensure-access-token", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] is not None
        assert response.json()["user_id"] is not None
        assert response.json()["is_authenticated"] is False

    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_token(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()

        headers = {"Authorization": f"Bearer invalid_token"}

        response = await async_client.post("/api/access-token/ensure-access-token", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] is not None
        assert response.json()["user_id"] is not None
        assert response.json()["is_authenticated"] is False

    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_token(self, async_client, service_container: ServiceContainer):
        response = await async_client.post("/api/access-token/ensure-access-token")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] is not None
        assert response.json()["user_id"] is not None
        assert response.json()["is_authenticated"] is False
        
        headers = {}
        response = await async_client.post("/api/access-token/ensure-access-token", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] is not None
        assert response.json()["user_id"] is not None
        assert response.json()["is_authenticated"] is False
        
        headers = {"Authorization": "Bearer "}
        response = await async_client.post("/api/access-token/ensure-access-token", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] is not None
        assert response.json()["user_id"] is not None
        assert response.json()["is_authenticated"] is False 
        
        headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.post("/api/access-token/ensure-access-token", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] is not None
        assert response.json()["user_id"] is not None
        assert response.json()["is_authenticated"] is False

    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_format(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()

        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/access-token/ensure-access-token", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] is not None
        assert response.json()["user_id"] is not None
        assert response.json()["is_authenticated"] is False
