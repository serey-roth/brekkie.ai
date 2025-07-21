from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.schema import DBUser

from schemas.users import CreateUserParams

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

