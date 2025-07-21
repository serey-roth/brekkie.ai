from datetime import datetime
from pydantic import BaseModel, Field


class User(BaseModel):
    id: str = Field(description="Unique identifier for the user")
    created_at: str = Field(description="When the user was created")
    updated_at: str = Field(description="When the user was last modified")
    external_id: str = Field(description="The ID of the user in the external authentication provider")

class CreateUserParams(User):
    id: str = Field(description="Unique identifier for the user")
    created_at: datetime = Field(description="When the user was created")
    updated_at: datetime = Field(description="When the user was last modified")
    external_id: str = Field(description="The ID of the user in the external authentication provider")