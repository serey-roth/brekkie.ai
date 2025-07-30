from datetime import datetime

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str = Field(description="Unique identifier for the user")
    external_id: str = Field(description="The user's ID from the authentication provider")
    created_at: str = Field(description="When the user was created")
    updated_at: str = Field(description="When the user was last modified")
    last_signed_in_at: str | None = Field(description="When the user was last signed in")
    email: str | None = Field(description="The user's email address")
    name: str | None = Field(description="The user's name")

class CreateUserParams(BaseModel):
    id: str = Field(description="Unique identifier for the user")
    external_id: str = Field(description="The user's ID from the authentication provider")
    created_at: datetime = Field(description="When the user was created")
    updated_at: datetime = Field(description="When the user was last modified")
    last_signed_in_at: datetime | None = Field(description="When the user was last signed in")
    email: str | None = Field(description="The user's email address")
    name: str | None = Field(description="The user's name")

class UpdateUserParams(BaseModel):
    id: str = Field(description="Unique identifier for the user")
    external_id: str  = Field(description="The user's ID from the authentication provider")
    updated_at: datetime = Field(description="When the user was last modified")
    last_signed_in_at: datetime | None = Field(description="When the user was last signed in")
    email: str | None = Field(description="The user's email address")
    name: str | None = Field(description="The user's name")
