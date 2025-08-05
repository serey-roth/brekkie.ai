from typing import Annotated, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    environment: Annotated[
        Literal["development", "production", "test", "staging"],
        Field(default="production", alias="ENVIRONMENT"),
    ]

    # Database
    db_url: Annotated[
        str,
        Field(
            default="postgresql+psycopg://foodagent:fOoDaGent123@localhost:5432/foodagent",
            alias="DB_URL",
        ),
    ]
    checkpoint_db_url: Annotated[
        str,
        Field(
            default="postgresql://foodagent:fOoDaGent123@localhost:5432/foodagent",
            alias="CHECKPOINT_DB_URL",
        ),
    ]

    # Redis
    redis_url: Annotated[str, Field(default="redis://localhost:6379/", alias="REDIS_URL")]

    # API Keys
    google_api_key: str = Field(default="GOOGLE_API_KEY", alias="GOOGLE_API_KEY")
    tavily_api_key: str = Field(default="TAVILY_API_KEY", alias="TAVILY_API_KEY")

    # Cache TTL Settings (in seconds)
    thread_cache_ttl: int = 60 * 60 * 24  # 1 day
    message_cache_ttl: int = 60 * 60 * 24  # 1 day
    recipe_cache_ttl: int = 60 * 60 * 24  # 1 day
    user_access_cache_ttl: int = 60 * 60 * 24  # 1 day

    # Session and Limits
    session_ttl: int = 60 * 30  # 30 minutes
    authenticated_user_message_limit: int = 25
    unauthenticated_user_message_limit: int = 10
    
    # Redis Stream
    chat_session_data_stream: str = "brekkie_ai_chat_session_data_stream"
    chat_session_data_stream_group: str = "brekkie_ai_chat_session_data_stream_group"
    chat_session_data_stream_consumer: str = "brekkie_ai_chat_session_data_stream_consumer"

    # Cookie Settings
    cookie_name: str = "bk_access_token"
    cookie_max_age: int = 60 * 60 * 24  # 1 day
    cookie_samesite: str = "Lax"
    cookie_path: str = "/"

    # Refresh TTL
    access_token_refresh_ttl: int = 60 * 60 * 3  # 3 hours

    # Database Pool Settings
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # Environment-specific database pool settings
    def get_db_pool_size(self) -> int:
        if self.is_staging():
            return 2  # More conservative for staging
        return 5

    def get_db_max_overflow(self) -> int:
        if self.is_staging():
            return 3  # More conservative for staging
        return 10

    # Feature Flags
    enable_auth: bool = Field(default=True, alias="ENABLE_AUTH")
    supabase_url: str = Field(default="supabase_url", alias="SUPABASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        frozen=True,
        extra="ignore",
    )

    def __init__(self, env_file: str = ".env"):
        super().__init__(_env_file=env_file)

    def is_production(self) -> bool:
        return self.environment == "production"

    def is_development(self) -> bool:
        return self.environment == "development"

    def is_test(self) -> bool:
        return self.environment == "test"

    def is_staging(self) -> bool:
        return self.environment == "staging"

    def get_cookie_secure(self) -> bool:
        return self.is_production() or self.is_staging()

    def get_cookie_samesite(self) -> str:
        return self.cookie_samesite

    def get_cookie_httponly(self) -> bool:
        return self.is_production()

    def is_auth_enabled(self) -> bool:
        if self.is_production():
            return False
        return self.enable_auth


def create_settings(env_file: str = ".env") -> Settings:
    """Create Settings instance with custom env file."""
    return Settings(env_file=env_file)
