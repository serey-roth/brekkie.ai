from datetime import datetime
from typing import cast

from database.schema import DBUser
from repositories.user_repository import UserRepository
from schemas.users import (
    CreateUserParams,
    UpdateUserParams,
    User,
)
from sqlalchemy.ext.asyncio import AsyncSession
from utils.date_utils import to_utc_isostring
from utils.logger import Logger

logger = Logger("user_service")


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def _to_user_dto(self, user: DBUser) -> User:
        return User(
            id=str(user.id),
            external_id=str(user.external_id),
            created_at=to_utc_isostring(cast(datetime, user.created_at)),
            updated_at=to_utc_isostring(cast(datetime, user.updated_at)),
            last_signed_in_at=to_utc_isostring(cast(datetime, user.last_signed_in_at)) if user.last_signed_in_at is not None else None,
            email=str(user.email) if user.email is not None else None,
            name=str(user.name) if user.name is not None else None
        )

    async def create_user(self, db: AsyncSession, params: CreateUserParams) -> User:
        logger.debug(f"Creating user with external_id: {params.external_id}")
        user = await self.repository.create_user(db, params)
        return self._to_user_dto(user)

    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> User | None:
        logger.debug(f"Getting user by id: {user_id}")
        user = await self.repository.get_user_by_id(db, user_id)
        return self._to_user_dto(user) if user else None

    async def get_user_by_external_id(self, db: AsyncSession, external_id: str) -> User | None:
        logger.debug(f"Getting user by external_id: {external_id}")
        user = await self.repository.get_user_by_external_id(db, external_id)
        return self._to_user_dto(user) if user else None

    async def update_user(self, db: AsyncSession, user_id: str, params: UpdateUserParams) -> User:
        logger.debug(f"Updating user with id: {user_id}")
        user = await self.repository.update_user(db, user_id, params)
        return self._to_user_dto(user)
