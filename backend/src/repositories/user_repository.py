from database.schema import DBUser
from schemas.users import CreateUserParams, UpdateUserParams
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.date_utils import strip_timezone


class UserRepository:
    """Repository for user account operations including creation, retrieval, and updates."""

    async def create_user(self, db: AsyncSession, params: CreateUserParams) -> DBUser:
        existing_user = await self.get_user_by_external_id(db, params.external_id)
        if existing_user is not None:
            raise ValueError(f"External ID {params.external_id} already in use")
        
        new_user = DBUser(
            id=params.id,
            created_at=strip_timezone(params.created_at),
            updated_at=strip_timezone(params.updated_at),
            external_id=params.external_id,
            email=params.email,
            last_signed_in_at=strip_timezone(params.last_signed_in_at) if params.last_signed_in_at is not None else None,
            name=params.name
        )
        db.add(new_user)
        await db.flush()
        return new_user

    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> DBUser | None:
        result = await db.execute(select(DBUser).where(DBUser.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_external_id(self, db: AsyncSession, external_id: str) -> DBUser | None:
        result = await db.execute(select(DBUser).where(DBUser.external_id == external_id))
        return result.scalar_one_or_none()

    async def update_user(self, db: AsyncSession, user_id: str, params: UpdateUserParams) -> DBUser:
        user = await self.get_user_by_id(db, user_id)
        if user is None:
            raise ValueError(f"User with ID {user_id} not found")
        
        for key, value in params.model_dump().items():
            if value is None:
                continue
            
            if key == "updated_at" or key == "last_signed_in_at":
                setattr(user, key, strip_timezone(value))
            else:
                setattr(user, key, value)

        db.add(user)
        await db.flush()
        return user
    