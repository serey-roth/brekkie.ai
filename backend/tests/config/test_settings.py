import pytest
import os
from config.settings import Settings, get_settings, reset_settings


class TestSettings:
    def test_default_values(self):
        """Test that default values are set correctly."""
        settings = Settings()
        
        # Test environment defaults
        assert settings.environment == "production"
        
        # Test cache TTL defaults
        assert settings.thread_cache_ttl == 60 * 60 * 24 * 3  # 3 days
        assert settings.message_cache_ttl == 60 * 60 * 24 * 3  # 3 days
        assert settings.recipe_cache_ttl == 60 * 60 * 24 * 3  # 3 days
        assert settings.user_access_cache_ttl == 60 * 60 * 24 * 3  # 3 days
        
        # Test rate limiting defaults
        assert settings.anonymous_access_rate_limiter_ttl == 60 * 60  # 1 hour
        assert settings.anonymous_access_rate_limiter_limit == 10
        
        # Test session defaults
        assert settings.session_ttl == 60 * 30  # 30 minutes
        assert settings.authenticated_user_message_limit == 50
        assert settings.unauthenticated_user_message_limit == 10
        
        # Test cookie defaults
        assert settings.cookie_max_age == 60 * 60 * 24 * 3  # 3 days
        assert settings.cookie_secure is True
        assert settings.cookie_samesite == "Lax"
        assert settings.cookie_httponly is True
        
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
        os.environ["COOKIE_SECURE"] = "false"
        
        try:
            settings = Settings()
            
            assert settings.thread_cache_ttl == 3600
            assert settings.authenticated_user_message_limit == 100
            assert settings.cookie_secure is False
        finally:
            # Clean up environment variables
            os.environ.pop("THREAD_CACHE_TTL", None)
            os.environ.pop("AUTHENTICATED_USER_MESSAGE_LIMIT", None)
            os.environ.pop("COOKIE_SECURE", None)

    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        reset_settings()  # Reset for clean test
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2

    def test_reset_settings(self):
        """Test that reset_settings creates a new instance."""
        settings1 = get_settings()
        reset_settings()
        settings2 = get_settings()
        
        assert settings1 is not settings2 