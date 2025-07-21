import pytest
from unittest.mock import AsyncMock, MagicMock

from services.chat_services.chat_session_limit_checker import ChatSessionLimitChecker
from services.data_services.user_access_cache_service import UserAccessCacheService
from schemas.user_access import UserAccess
from schemas.chat_session_errors import AccessTokenNotFoundError


@pytest.fixture
def mock_user_access_cache_service():
    return MagicMock(spec=UserAccessCacheService)


@pytest.fixture
def chat_session_limit_checker(mock_user_access_cache_service):
    return ChatSessionLimitChecker(
        authenticated_user_message_limit=100,
        unauthenticated_user_message_limit=10,
        user_access_cache_service=mock_user_access_cache_service
    )


class TestHasMessageLimitReached:
    @pytest.mark.asyncio
    async def test_authenticated_user_below_limit(self, chat_session_limit_checker, mock_user_access_cache_service):
        access_token = "test_token"
        user_access = UserAccess(
            access_token=access_token,
            user_id="user_id",
            is_authenticated=True,
            user_message_count=50
        )
        
        mock_user_access_cache_service.get_user_access.return_value = user_access
        
        result = await chat_session_limit_checker.has_message_limit_reached(access_token)
        
        assert result is False
        mock_user_access_cache_service.get_user_access.assert_called_once_with(access_token)

    @pytest.mark.asyncio
    async def test_authenticated_user_at_limit(self, chat_session_limit_checker, mock_user_access_cache_service):
        access_token = "test_token"
        user_access = UserAccess(
            access_token=access_token,
            user_id="user_id",
            is_authenticated=True,
            user_message_count=100
        )
        
        mock_user_access_cache_service.get_user_access.return_value = user_access
        
        result = await chat_session_limit_checker.has_message_limit_reached(access_token)
        
        assert result is True
        mock_user_access_cache_service.get_user_access.assert_called_once_with(access_token)

    @pytest.mark.asyncio
    async def test_authenticated_user_above_limit(self, chat_session_limit_checker, mock_user_access_cache_service):
        access_token = "test_token"
        user_access = UserAccess(
            access_token=access_token,
            user_id="user_id",
            is_authenticated=True,
            user_message_count=150
        )
        
        mock_user_access_cache_service.get_user_access.return_value = user_access
        
        result = await chat_session_limit_checker.has_message_limit_reached(access_token)
        
        assert result is True
        mock_user_access_cache_service.get_user_access.assert_called_once_with(access_token)

    @pytest.mark.asyncio
    async def test_unauthenticated_user_below_limit(self, chat_session_limit_checker, mock_user_access_cache_service):
        access_token = "test_token"
        user_access = UserAccess(
            access_token=access_token,
            user_id="user_id",
            is_authenticated=False,
            user_message_count=5
        )
        
        mock_user_access_cache_service.get_user_access.return_value = user_access
        
        result = await chat_session_limit_checker.has_message_limit_reached(access_token)
        
        assert result is False
        mock_user_access_cache_service.get_user_access.assert_called_once_with(access_token)

    @pytest.mark.asyncio
    async def test_unauthenticated_user_at_limit(self, chat_session_limit_checker, mock_user_access_cache_service):
        access_token = "test_token"
        user_access = UserAccess(
            access_token=access_token,
            user_id="user_id",
            is_authenticated=False,
            user_message_count=10
        )
        
        mock_user_access_cache_service.get_user_access.return_value = user_access
        
        result = await chat_session_limit_checker.has_message_limit_reached(access_token)
        
        assert result is True
        mock_user_access_cache_service.get_user_access.assert_called_once_with(access_token)

    @pytest.mark.asyncio
    async def test_unauthenticated_user_above_limit(self, chat_session_limit_checker, mock_user_access_cache_service):
        access_token = "test_token"
        user_access = UserAccess(
            access_token=access_token,
            user_id="user_id",
            is_authenticated=False,
            user_message_count=15
        )
        
        mock_user_access_cache_service.get_user_access.return_value = user_access
        
        result = await chat_session_limit_checker.has_message_limit_reached(access_token)
        
        assert result is True
        mock_user_access_cache_service.get_user_access.assert_called_once_with(access_token)

    @pytest.mark.asyncio
    async def test_access_token_not_found(self, chat_session_limit_checker, mock_user_access_cache_service):
        access_token = "invalid_token"
        mock_user_access_cache_service.get_user_access.return_value = None
        
        with pytest.raises(AccessTokenNotFoundError) as exc_info:
            await chat_session_limit_checker.has_message_limit_reached(access_token)
        
        assert exc_info.value.access_token == access_token
        mock_user_access_cache_service.get_user_access.assert_called_once_with(access_token)


class TestGetMessageLimit:
    @pytest.mark.asyncio
    async def test_authenticated_user_limit(self, chat_session_limit_checker, mock_user_access_cache_service):
        access_token = "test_token"
        user_access = UserAccess(
            access_token=access_token,
            user_id="user_id",
            is_authenticated=True,
            user_message_count=50
        )
        
        mock_user_access_cache_service.get_user_access.return_value = user_access
        
        result = await chat_session_limit_checker.get_message_limit(access_token)
        
        assert result == 100
        mock_user_access_cache_service.get_user_access.assert_called_once_with(access_token)

    @pytest.mark.asyncio
    async def test_unauthenticated_user_limit(self, chat_session_limit_checker, mock_user_access_cache_service):
        access_token = "test_token"
        user_access = UserAccess(
            access_token=access_token,
            user_id="user_id", 
            is_authenticated=False,
            user_message_count=5
        )
        
        mock_user_access_cache_service.get_user_access.return_value = user_access
        
        result = await chat_session_limit_checker.get_message_limit(access_token)
        
        assert result == 10
        mock_user_access_cache_service.get_user_access.assert_called_once_with(access_token)

    @pytest.mark.asyncio
    async def test_get_message_limit_access_token_not_found(self, chat_session_limit_checker, mock_user_access_cache_service):
        access_token = "invalid_token"
        mock_user_access_cache_service.get_user_access.return_value = None
        
        with pytest.raises(AccessTokenNotFoundError) as exc_info:
            await chat_session_limit_checker.get_message_limit(access_token)
        
        assert exc_info.value.access_token == access_token
        mock_user_access_cache_service.get_user_access.assert_called_once_with(access_token) 