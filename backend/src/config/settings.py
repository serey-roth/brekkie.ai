from typing import Annotated, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    environment: Annotated[
        Literal["development", "production", "test"],
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

    # API Keys
    google_api_key: str = Field(default="GOOGLE_API_KEY", alias="GOOGLE_API_KEY")

    # Limits
    user_message_limit: int | None = 15

    # Database Pool Settings
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    def get_db_pool_size(self) -> int:
        return 5

    def get_db_max_overflow(self) -> int:
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

    def is_auth_enabled(self) -> bool:
        return self.enable_auth


def create_settings(env_file: str = ".env") -> Settings:
    """Create Settings instance with custom env file."""
    return Settings(env_file=env_file)
