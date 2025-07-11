import os

from pydantic import ValidationError

import pytest

from config.settings import Settings, create_settings

class TestDefaultValues:
    def test_default_values(self):
        """Test that default values are set correctly."""
        settings = create_settings()
                
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
        assert settings.cookie_samesite == "Lax"
        
        # Test database pool defaults
        assert settings.db_pool_size == 5
        assert settings.db_max_overflow == 10
        assert settings.db_pool_timeout == 30
        assert settings.db_pool_recycle == 3600
        
        assert settings.access_token_refresh_ttl == 60 * 60 * 3  # 3 hours
        
        assert settings.prompt_injection_model_id == "ProtectAI/deberta-v3-base-prompt-injection-v2"
        assert settings.toxicity_model_id == "unitary/toxic-bert"   
        
    def test_override_settings(self):
        os.environ["ENVIRONMENT"] = "production"
        os.environ["DB_URL"] = "postgresql://foodagent:fOoDaGent123@localhost:5432/test_db_url"
        os.environ["CHECKPOINT_DB_URL"] = "postgresql://foodagent:fOoDaGent123@localhost:5432/test_checkpoint_db_url"
        os.environ["REDIS_URL"] = "redis://localhost:6379/test_redis_url"
        os.environ["GOOGLE_API_KEY"] = "test_google_api_key"
        os.environ["TAVILY_API_KEY"] = "test_tavily_api_key"
        os.environ["ENABLE_AUTH"] = "true"
        
        try:
            settings = create_settings(".env.test")
            assert settings.environment == "production"
            assert str(settings.db_url) == "postgresql://foodagent:fOoDaGent123@localhost:5432/test_db_url"
            assert str(settings.checkpoint_db_url) == "postgresql://foodagent:fOoDaGent123@localhost:5432/test_checkpoint_db_url"
            assert str(settings.redis_url) == "redis://localhost:6379/test_redis_url"
            assert settings.google_api_key == "test_google_api_key"
            assert settings.tavily_api_key == "test_tavily_api_key"
            assert settings.enable_auth is True
        finally:
            os.environ.pop("ENVIRONMENT")
            os.environ.pop("DB_URL")
            os.environ.pop("CHECKPOINT_DB_URL")
            os.environ.pop("REDIS_URL")
            os.environ.pop("GOOGLE_API_KEY")
            os.environ.pop("TAVILY_API_KEY")
            os.environ.pop("ENABLE_AUTH")
        

class TestMutateSettings:
    def test_mutate_settings(self):
        settings = create_settings(".env.test")
        with pytest.raises(ValidationError):
            settings.enable_auth = True
     
     
class TestDevelopmentSettings:
    @pytest.fixture
    def settings(self):
        return create_settings(".env.development")
    
    def test_environment(self, settings: Settings):
        assert settings.environment == "development"
        
    def test_db_url(self, settings: Settings):
        assert str(settings.db_url) == "postgresql+psycopg://foodagent:fOoDaGent123@localhost:5432/foodagent"
        
    def test_checkpoint_db_url(self, settings: Settings):
        assert str(settings.checkpoint_db_url) == "postgresql://foodagent:fOoDaGent123@localhost:5432/foodagent"
        
    def test_redis_url(self, settings: Settings):
        assert str(settings.redis_url) == "redis://localhost:6379/"
        
    def test_is_development(self, settings: Settings):
        assert settings.is_development() is True
        
    def test_is_production(self, settings: Settings):
        assert settings.is_production() is False
        
    def test_is_test(self, settings: Settings):
        assert settings.is_test() is False
        
    def test_get_cookie_secure_method(self, settings: Settings):
        assert settings.get_cookie_secure() is False
        
    def test_get_cookie_httponly_method(self, settings: Settings):
        assert settings.get_cookie_httponly() is False
        
    def test_is_auth_enabled_method(self, settings: Settings):
        assert settings.is_auth_enabled() is False
        

class TestProductionSettings:
    @pytest.fixture
    def settings(self):
        return create_settings(".env.production")
    
    def test_environment(self, settings: Settings):
        assert settings.environment == "production"
        
    def test_db_url(self, settings: Settings):
        assert str(settings.db_url) != "postgresql://foodagent:fOoDaGent123@localhost:5432/foodagent"
        
    def test_checkpoint_db_url(self, settings: Settings):
        assert str(settings.checkpoint_db_url) != "postgresql://foodagent:fOoDaGent123@localhost:5432/foodagent"
        
    def test_redis_url(self, settings: Settings):
        assert str(settings.redis_url) != "redis://localhost:6379"
        
    def test_api_keys(self, settings: Settings):
        assert settings.google_api_key != "GOOGLE_API_KEY"
        assert settings.tavily_api_key != "TAVILY_API_KEY"
        
    def test_is_production(self, settings: Settings):
        assert settings.is_production() is True
        
    def test_is_development(self, settings: Settings):
        assert settings.is_development() is False
        
    def test_is_test(self, settings: Settings):
        assert settings.is_test() is False
        
    def test_get_cookie_secure_method(self, settings: Settings):
        assert settings.get_cookie_secure() is True
        
    def test_get_cookie_httponly_method(self, settings: Settings):
        assert settings.get_cookie_httponly() is True
        
    def test_is_auth_enabled_method(self, settings: Settings):
        assert settings.is_auth_enabled() is False
        
        
class TestTestSettings:
    @pytest.fixture
    def settings(self):
        return create_settings(".env.test")
    
    def test_environment(self, settings: Settings):
        assert settings.environment == "test"
        
    def test_db_url(self, settings: Settings):
        assert str(settings.db_url) == "postgresql+psycopg://foodagent:fOoDaGent123@localhost:5432/foodagent"
        
    def test_checkpoint_db_url(self, settings: Settings):
        assert str(settings.checkpoint_db_url) == "postgresql://foodagent:fOoDaGent123@localhost:5432/foodagent"
        
    def test_redis_url(self, settings: Settings):
        assert str(settings.redis_url) == "redis://localhost:6379/"
        
    def test_api_keys(self, settings: Settings):
        assert settings.google_api_key != "GOOGLE_API_KEY"
        assert settings.tavily_api_key != "TAVILY_API_KEY"

    def test_is_production(self, settings: Settings):
        assert settings.is_production() is False
        
    def test_is_development(self, settings: Settings):
        assert settings.is_development() is False
        
    def test_is_test(self, settings: Settings):
        assert settings.is_test() is True

    def test_get_cookie_secure_method(self, settings: Settings):
        assert settings.get_cookie_secure() is False

    def test_get_cookie_httponly_method(self, settings: Settings):
        assert settings.get_cookie_httponly() is False

    def test_is_auth_enabled_method(self, settings: Settings):
        assert settings.is_auth_enabled() is False


