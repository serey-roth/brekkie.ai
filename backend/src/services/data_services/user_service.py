from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_repository import UserRepository

from schemas.users import (
    CreateDbUserParams,
    UpdateDbUserParams,
    User,
    CreateUserParams,
    UpdateUserParams,
)

from utils.logger import Logger
import utils.password as password_utils

logger = Logger("user_service")


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
        
    
    async def create_user(self, db: AsyncSession, params: CreateUserParams) -> User:
        logger.debug(f"Creating user with email: {params.email}")
        password_hash = password_utils.hash_password(params.password) if params.password else None
        user = await self.repository.create_user(db, CreateDbUserParams(
            id=params.id,
            email=params.email,
            name=params.name,
            password_hash=password_hash,
            created_at=params.created_at,
            updated_at=params.updated_at,
        ))
        return User.from_db_user(user)
    
    
    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> User | None:
        logger.debug(f"Getting user by id: {user_id}")
        user = await self.repository.get_user_by_id(db, user_id)
        return User.from_db_user(user) if user else None
    
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> User | None:
        logger.debug(f"Getting user by email: {email}")
        user = await self.repository.get_user_by_email(db, email)
        return User.from_db_user(user) if user else None
    
 
    async def update_user(self, db: AsyncSession, params: UpdateUserParams) -> User:
        logger.debug(f"Updating user {params.id}")
        password_hash = password_utils.hash_password(params.password) if params.password else None
        user = await self.repository.update_user(db, UpdateDbUserParams(
            id=params.id,
            updated_at=params.updated_at,
            email=params.email,
            name=params.name,
            password_hash=password_hash,
        ))
        return User.from_db_user(user)
    
    
    async def verify_password(self, db: AsyncSession, user_id: str, password: str) -> bool:
        logger.debug(f"Verifying password for user {user_id}")
        user = await self.repository.get_user_by_id(db, user_id)
        if not user or not user.password_hash:
            return False
        return password_utils.verify_password(password, user.password_hash)
    