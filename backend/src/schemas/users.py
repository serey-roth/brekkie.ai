from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class User(BaseModel):
    id: str
    email: str | None
    name: str | None
    created_at: str
    updated_at: str


class UserSignup(BaseModel):
    email: EmailStr
    name: str
    password: str
    confirm_password: str

    @field_validator("email")
    def validate_email(cls, v):
        if not v:
            raise ValueError("Email is required")
        return v

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

    @field_validator("name")
    def validate_name(cls, v):
        if not v:
            raise ValueError("Name is required")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    def validate_email(cls, v):
        if not v:
            raise ValueError("Email is required")
        return v

    @field_validator("password")
    def validate_password(cls, v):
        if not v:
            raise ValueError("Password is required")
        return v


class BaseCreateUserParams(BaseModel):
    """Parameters for creating a new user account."""

    id: str = Field(description="Unique identifier for the user account")
    created_at: datetime = Field(description="When the user account was created")
    updated_at: datetime = Field(description="When the user account was last modified")


class CreateUserParams(BaseCreateUserParams):
    email: EmailStr = Field(description="User's email address, must be unique")
    name: str = Field(description="User's display name or full name")
    password: str = Field(description="User's password")


class CreateDbUserParams(BaseCreateUserParams):
    email: str = Field(description="User's email address, must be unique")
    name: str = Field(description="User's display name or full name")
    password_hash: str = Field(description="Bcrypt-hashed password")


class BaseUpdateUserParams(BaseModel):
    """Parameters for updating an existing user's profile information."""

    id: str = Field(description="Unique identifier of the user to update")
    updated_at: datetime = Field(description="When the user account was last modified")


class UpdateUserParams(BaseUpdateUserParams):
    email: EmailStr | None = Field(default=None, description="User's email address, must be unique")
    name: str | None = Field(default=None, description="User's display name or full name")
    password: str | None = Field(default=None, description="User's password")


class UpdateDbUserParams(BaseUpdateUserParams):
    email: EmailStr | None = Field(default=None, description="User's email address, must be unique")
    name: str | None = Field(default=None, description="User's display name or full name")
    password_hash: str | None = Field(default=None, description="Bcrypt-hashed password")
