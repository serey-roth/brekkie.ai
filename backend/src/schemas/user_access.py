from datetime import datetime, timezone
from pydantic import BaseModel, Field

from utils.date_utils import to_utc_isostring

class UserAccessData(BaseModel):
    access_token: str = Field(description="The access token for the user")
    user_id: str = Field(description="The ID of the user")
    name: str | None = Field(default=None, description="The name of the user")
    email: str | None = Field(default=None, description="The email of the user")
    is_authenticated: bool = Field(default=False, description="Whether the user is authenticated")
    user_message_count: int = Field(default=0, description="The number of messages the user has sent")
    created_at: str = Field(default_factory=lambda: to_utc_isostring(datetime.now(timezone.utc)), description="The timestamp when the user access was created")
    updated_at: str = Field(default_factory=lambda: to_utc_isostring(datetime.now(timezone.utc)), description="The timestamp when the user access was last updated")
    ip_address: str | None = Field(default=None, description="The IP address of the user")
    