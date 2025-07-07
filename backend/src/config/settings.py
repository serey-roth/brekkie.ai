import os
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Environment
    environment: Literal["development", "production"] = Field(default="production", env="ENVIRONMENT")
    
    # Database
    db_url: Optional[str] = Field(default=None, env="DB_URL")
    checkpoint_db_url: Optional[str] = Field(default=None, env="CHECKPOINT_DB_URL")
    
    # Redis
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # API Keys
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    tavily_api_key: Optional[str] = Field(default=None, env="TAVILY_API_KEY")
    
    # Cache TTL Settings (in seconds)
    thread_cache_ttl: int = Field(default=60 * 60 * 24 * 3, env="THREAD_CACHE_TTL")  # 3 days
    message_cache_ttl: int = Field(default=60 * 60 * 24 * 3, env="MESSAGE_CACHE_TTL")  # 3 days
    recipe_cache_ttl: int = Field(default=60 * 60 * 24 * 3, env="RECIPE_CACHE_TTL")  # 3 days
    user_access_cache_ttl: int = Field(default=60 * 60 * 24 * 3, env="USER_ACCESS_CACHE_TTL")  # 3 days
    
    # Rate Limiting
    anonymous_access_rate_limiter_ttl: int = Field(default=60 * 60, env="ANONYMOUS_ACCESS_RATE_LIMITER_TTL")  # 1 hour
    anonymous_access_rate_limiter_limit: int = Field(default=10, env="ANONYMOUS_ACCESS_RATE_LIMITER_LIMIT")
    
    # Session and Limits
    session_ttl: int = Field(default=60 * 30, env="SESSION_TTL")  # 30 minutes
    authenticated_user_message_limit: int = Field(default=50, env="AUTHENTICATED_USER_MESSAGE_LIMIT")
    unauthenticated_user_message_limit: int = Field(default=10, env="UNAUTHENTICATED_USER_MESSAGE_LIMIT")
    
    # Cookie Settings
    cookie_name: str = Field(default="bk_access_token", env="COOKIE_NAME")
    cookie_max_age: int = Field(default=60 * 60 * 24 * 3, env="COOKIE_MAX_AGE")  # 3 days
    cookie_samesite: str = Field(default="Lax", env="COOKIE_SAMESITE")
    cookie_path: str = Field(default="/", env="COOKIE_PATH")
    
    # Refresh TTL
    access_token_refresh_ttl: int = Field(default=60 * 60 * 3, env="ACCESS_TOKEN_REFRESH_TTL")  # 3 hours
    
    # Database Pool Settings
    db_pool_size: int = Field(default=5, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


    def is_production(self) -> bool:
        return self.environment == "production"
    
    def is_development(self) -> bool:
        return self.environment == "development"
    
    def get_cookie_secure(self) -> bool:
        return self.is_production()
    
    def get_cookie_httponly(self) -> bool:
        return self.is_production()
    

# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance, creating it if necessary."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance (useful for testing)."""
    global _settings
    _settings = None


def set_settings(settings: Settings) -> None:
    """Set the global settings instance (useful for testing)."""
    global _settings
    _settings = settings 
    