from typing import cast
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from database.schema import DBUser

from repositories.user_repository import UserRepository

from schemas.users import (
    User,
    CreateUserParams,
)

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
