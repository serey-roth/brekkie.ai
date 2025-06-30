from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession 

from database.schema import DBUser

from schemas.users import (
    CreateDbUserParams,
    UpdateDbUserParams,
)

from utils.date_utils import strip_timezone


class UserRepository:
    """Repository for user account operations including creation, retrieval, and updates."""
    
    async def create_user(self, db: AsyncSession, params: CreateDbUserParams) -> DBUser:
        """Creates a new user record with the provided parameters.
        
        Args:
            db: Database session for the operation
            params: User creation parameters including id, email, name, and password_hash
            
        Returns:
            The newly created user record
            
        Raises:
            ValueError: If the email is already in use by another user
        """
        if await self.get_user_by_email(db, params.email):
            raise ValueError(f"Email {params.email} already in use")
        
        new_user = DBUser(
            created_at=strip_timezone(params.created_at),
            updated_at=strip_timezone(params.updated_at),
            **params.model_dump(exclude={"created_at", "updated_at"}, exclude_none=True, exclude_unset=True)
        )
        db.add(new_user)
        await db.flush()
        return new_user


    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> DBUser | None:
        """Gets a user record with the given id.
        
        Args:
            db: Database session for the operation
            user_id: The user's id
            
        Returns:
            User record if found, None otherwise
        """
        result = await db.execute(select(DBUser).where(DBUser.id == user_id))
        return result.scalar_one_or_none()


    async def get_user_by_email(self, db: AsyncSession, email: str) -> DBUser | None:
        """Gets a user record with the given email address.
        
        Args:
            db: Database session for the operation
            email: The user's email address
            
        Returns:
            User record if found, None otherwise
        """
        result = await db.execute(select(DBUser).where(DBUser.email == email))
        return result.scalar_one_or_none()


    async def update_user(self, db: AsyncSession, params: UpdateDbUserParams) -> DBUser:
        """Updates an existing user record with the given parameters.
        
        Args:
            db: Database session for the operation
            params: Update parameters containing the user id and fields to update
            
        Returns:
            The updated user record
            
        Raises:
            ValueError: If the user doesn't exist or if the new email is already in use
        """
        user_id = params.id
        updated_at = params.updated_at
        
        db_user = await db.get(DBUser, user_id)
        if db_user is None:
            raise ValueError(f"User {user_id} not found")
        
        if params.email:
            existing_user = await self.get_user_by_email(db, params.email)
            if existing_user and existing_user.id != user_id:
                raise ValueError(f"Email {params.email} already in use")
            
        items_to_update = params.model_dump(exclude={"id", "updated_at"}, exclude_none=True, exclude_unset=True)
        for field, value in items_to_update.items():
            setattr(db_user, field, value)
        
        db_user.updated_at = strip_timezone(updated_at)
        
        await db.flush()
        return db_user
