from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from database.schema import DBUser

from utils.date_utils import to_utc_isostring


class User(BaseModel):
    id: str
    email: str | None
    name: str | None
    created_at: str
    updated_at: str
    
    @staticmethod
    def from_db_user(user: DBUser) -> "User":
        return User(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=to_utc_isostring(user.created_at),
            updated_at=to_utc_isostring(user.updated_at),
        )

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

    @model_validator(mode='after')
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
    


class BaseUserParams(BaseModel):
    """Base parameters for user operations."""
    email: str | None = Field(default=None, description="User's email address, must be unique")
    name: str | None = Field(default=None, description="User's display name or full name")
    
    
class BaseUserParamsWithRawPassword(BaseUserParams):
    password: str | None = Field(default=None, description="User's password")
    
    
class BaseUserParamsWithHashedPassword(BaseUserParams):
    password_hash: str | None = Field(default=None, description="Bcrypt-hashed password")
    
    
class BaseCreateUserParams(BaseModel):
    """Parameters for creating a new user account."""
    id: str = Field(description="Unique identifier for the user account")
    created_at: datetime = Field(description="When the user account was created")
    updated_at: datetime = Field(description="When the user account was last modified")
    
    
class CreateUserParams(BaseCreateUserParams, BaseUserParamsWithRawPassword):
    pass


class CreateDbUserParams(BaseCreateUserParams, BaseUserParamsWithHashedPassword):
    pass
    
    
class BaseUpdateUserParams(BaseModel):
    """Parameters for updating an existing user's profile information."""
    id: str = Field(description="Unique identifier of the user to update")
    updated_at: datetime = Field(description="When the user account was last modified")
    

class UpdateUserParams(BaseUpdateUserParams, BaseUserParamsWithRawPassword):
    pass


class UpdateDbUserParams(BaseUpdateUserParams, BaseUserParamsWithHashedPassword):
    pass
