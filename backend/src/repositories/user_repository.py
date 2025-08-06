from database.schema import DBUser
from schemas.users import CreateUserParams, UpdateUserParams
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.date_utils import strip_timezone


class UserRepository:
    """Repository for user account operations including creation, retrieval, and updates."""

    async def create_user(self, db: AsyncSession, params: CreateUserParams) -> DBUser:
        """Create a new user.

        Args:
            db: Database session for the operation
            params: User creation parameters including external_id, email, and name

        Returns:
            The newly created user
        """
        existing_user = await self.get_user_by_external_id(db, params.external_id)
        if existing_user is not None:
            raise ValueError(f"External ID {params.external_id} already in use")

        new_user = DBUser(
            id=params.id,
            created_at=strip_timezone(params.created_at),
            updated_at=strip_timezone(params.updated_at),
            external_id=params.external_id,
            email=params.email,
            last_signed_in_at=strip_timezone(params.last_signed_in_at)
            if params.last_signed_in_at is not None
            else None,
            name=params.name,
        )
        db.add(new_user)
        return new_user

    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> DBUser | None:
        """Get a user by their unique identifier.

        Args:
            db: Database session for the operation
            user_id: Unique identifier for the user

        Returns:
            The user record if found, None otherwise
        """
        result = await db.execute(select(DBUser).where(DBUser.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_external_id(self, db: AsyncSession, external_id: str) -> DBUser | None:
        """Get a user by their external ID.

        Args:
            db: Database session for the operation
            external_id: External ID for the user

        Returns:
            The user record if found, None otherwise
        """
        result = await db.execute(select(DBUser).where(DBUser.external_id == external_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, db: AsyncSession, email: str) -> DBUser | None:
        """Get a user by their email address.

        Args:
            db: Database session for the operation
            email: Email address for the user

        Returns:
            The user record if found, None otherwise
        """
        result = await db.execute(select(DBUser).where(DBUser.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_external_id_or_email(
        self, db: AsyncSession, external_id: str, email: str | None
    ) -> DBUser | None:
        """Get a user by their external ID or email address.

        Args:
            db: Database session for the operation
            external_id: External ID for the user
            email: Email address for the user

        Returns:
            The user record if found, None otherwise
        """
        result = await db.execute(
            select(DBUser).where(or_(DBUser.external_id == external_id, DBUser.email == email))
        )
        return result.scalar_one_or_none()

    async def update_user(self, db: AsyncSession, params: UpdateUserParams) -> DBUser:
        """Update an existing user record.

        Args:
            db: Database session for the operation
            params: User update parameters including id, external_id, email, and name

        Returns:
            The updated user record
        """
        user = await self.get_user_by_id(db, params.id)
        if user is None:
            raise ValueError(f"User with ID {params.id} not found")

        for key, value in params.model_dump(exclude_unset=True).items():
            if value is not None:
                if key == "updated_at" or key == "last_signed_in_at":
                    setattr(user, key, strip_timezone(value))
                else:
                    setattr(user, key, value)

        db.add(user)
        return user