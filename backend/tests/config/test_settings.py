import pytest
import os
from config.settings import Settings


class TestSettings:
    def test_default_values(self):
        """Test that default values are set correctly."""
        settings = Settings()
        
        # Test environment defaults
        assert settings.environment == "production"
        
        # Test cache TTL defaults
        assert settings.thread_cache_ttl == 60 * 60 * 24  # 1 day
        assert settings.message_cache_ttl == 60 * 60 * 24  # 1 day
        assert settings.recipe_cache_ttl == 60 * 60 * 24  # 1 day
        assert settings.user_access_cache_ttl == 60 * 60 * 24  # 1 day
        
        # Test rate limiting defaults
        assert settings.anonymous_access_rate_limiter_ttl == 60 * 60 * 24  # 1 day
        assert settings.anonymous_access_rate_limiter_limit == 1
        
        # Test session defaults
        assert settings.session_ttl == 60 * 30  # 30 minutes
        assert settings.authenticated_user_message_limit == 50
        assert settings.unauthenticated_user_message_limit == 10
        
        # Test cookie defaults
        assert settings.cookie_max_age == 60 * 60 * 24  # 1 day
        assert settings.get_cookie_secure() is True  # production default
        assert settings.cookie_samesite == "Lax"
        assert settings.get_cookie_httponly() is True  # production default
        
        # Test database pool defaults
        assert settings.db_pool_size == 5
        assert settings.db_max_overflow == 10
        assert settings.db_pool_timeout == 30
        assert settings.db_pool_recycle == 3600

    def test_environment_variable_override(self):
        """Test that environment variables can override defaults."""
        # Set environment variables
        os.environ["THREAD_CACHE_TTL"] = "3600"  # 1 hour
        os.environ["AUTHENTICATED_USER_MESSAGE_LIMIT"] = "100"
        os.environ["ENVIRONMENT"] = "development"
        
        try:
            settings = Settings()
            
            assert settings.thread_cache_ttl == 3600
            assert settings.authenticated_user_message_limit == 100
            assert settings.get_cookie_secure() is False  # development default
        finally:
            # Clean up environment variables
            os.environ.pop("THREAD_CACHE_TTL", None)
            os.environ.pop("AUTHENTICATED_USER_MESSAGE_LIMIT", None)
            os.environ.pop("ENVIRONMENT", None)

    def test_is_production_method(self):
        """Test the is_production method."""
        # Test production environment
        settings = Settings(environment="production")
        assert settings.is_production() is True
        assert settings.is_development() is False
        
        # Test development environment
        settings = Settings(environment="development")
        assert settings.is_production() is False
        assert settings.is_development() is True

    def test_get_cookie_secure_method(self):
        """Test the get_cookie_secure method."""
        # Test production environment - should be secure
        settings = Settings(environment="production")
        assert settings.get_cookie_secure() is True
        
        # Test development environment - should not be secure
        settings = Settings(environment="development")
        assert settings.get_cookie_secure() is False

    def test_get_cookie_httponly_method(self):
        """Test the get_cookie_httponly method."""
        # Test production environment - should be httponly
        settings = Settings(environment="production")
        assert settings.get_cookie_httponly() is True
        
        # Test development environment - should not be httponly
        settings = Settings(environment="development")
        assert settings.get_cookie_httponly() is False

    def test_is_auth_enabled_method(self):
        """Test the is_auth_enabled method."""
        # Test with auth disabled (default)
        settings = Settings()
        assert settings.is_auth_enabled() is False
        
        # Test with auth enabled
        settings = Settings(enable_auth=True)
        assert settings.is_auth_enabled() is True
        
        # Test with auth explicitly disabled
        settings = Settings(enable_auth=False)
        assert settings.is_auth_enabled() is False

    def test_environment_methods_with_env_vars(self):
        """Test environment methods work correctly with environment variables."""
        # Test production
        os.environ["ENVIRONMENT"] = "production"
        try:
            settings = Settings()
            assert settings.is_production() is True
            assert settings.is_development() is False
            assert settings.get_cookie_secure() is True
            assert settings.get_cookie_httponly() is True
        finally:
            os.environ.pop("ENVIRONMENT", None)
        
        # Test development
        os.environ["ENVIRONMENT"] = "development"
        try:
            settings = Settings()
            assert settings.is_production() is False
            assert settings.is_development() is True
            assert settings.get_cookie_secure() is False
            assert settings.get_cookie_httponly() is False
        finally:
            os.environ.pop("ENVIRONMENT", None)

    def test_auth_enabled_with_env_vars(self):
        """Test auth enabled works correctly with environment variables."""
        # Test with auth enabled
        os.environ["ENABLE_AUTH"] = "true"
        try:
            settings = Settings()
            assert settings.is_auth_enabled() is True
        finally:
            os.environ.pop("ENABLE_AUTH", None)
        
        # Test with auth disabled
        os.environ["ENABLE_AUTH"] = "false"
        try:
            settings = Settings()
            assert settings.is_auth_enabled() is False
        finally:
            os.environ.pop("ENABLE_AUTH", None)
