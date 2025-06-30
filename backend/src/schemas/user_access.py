from pydantic import BaseModel, Field

class UserAccessData(BaseModel):
    access_token: str = Field(description="The access token for the user")
    user_id: str = Field(description="The ID of the user")
    name: str | None = Field(default=None, description="The name of the user")
    email: str | None = Field(default=None, description="The email of the user")
    is_authenticated: bool = Field(default=False, description="Whether the user is authenticated")
    user_message_count: int = Field(default=0, description="The number of messages the user has sent")
    