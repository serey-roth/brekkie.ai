from datetime import datetime, timezone, timedelta
from typing import Any, cast

import pytest
import pytest_asyncio

from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from database.schema import DBRecipe

from repositories.recipe_repository import RecipeRepository

from schemas.message_content_type import MessageContentType
from schemas.message_role import MessageRole
from schemas.messages import CreateMessageParams
from services.data_services.recipe_service import RecipeService

from schemas.recipes import (
    CreateRecipeParams,
    RecipeCategory,
    UpdateRecipeFieldParams,
    UpdateRecipeParams,
    UserRecipe,
    RecipeField,
    RecipeIngredient,
    RecipeInstruction,
)

from tests.test_helpers.assert_deep_equal import assert_deep_equal
from utils.date_utils import to_utc_isostring


pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="function")
def recipe_service() -> RecipeService:
    return RecipeService(RecipeRepository())


@pytest.fixture(scope="function")
def sample_user_id() -> str:
    return "test-user-id"


@pytest.fixture(scope="function")
def sample_thread_id() -> str:
    return "test-thread-id"


@pytest.fixture(scope="function")
def sample_message_id() -> str:
    return "test-message-id"


@pytest.fixture(scope="function")
def sample_timestamps() -> tuple[datetime, datetime]:
    return (datetime.now(timezone.utc), datetime.now(timezone.utc))


@pytest.fixture(scope="function")
def sample_recipe_id() -> str:
    return "test-recipe-id"


@pytest.fixture(scope="function")
def sample_recipe(
    sample_recipe_id: str,
    sample_user_id: str,
    sample_thread_id: str,
    sample_timestamps: tuple[datetime, datetime],
) -> dict[str, Any]:
    return {
        "id": sample_recipe_id,
        "user_id": sample_user_id,
        "thread_id": sample_thread_id,
        "created_at": sample_timestamps[0].replace(tzinfo=None),
        "updated_at": sample_timestamps[1].replace(tzinfo=None),
        "name": "test-name",
        "description": "test-description",
        "ingredients": [
            {
                "name": "test-ingredient-name",
                "quantity": "test-ingredient-quantity",
                "unit": "test-ingredient-unit",
            }
        ],
        "instructions": [
            {
                "title": "test-instruction-title",
                "description": "test-instruction-description",
            }
        ],
        "categories": [
            {
                "name": "test-category-name",
            }
        ],
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "servings": "4",
    }


class TestCreateRecipes:
    async def test_create_recipes(
        self,
        recipe_service: RecipeService,
        async_session: AsyncSession,
        sample_user_id: str,
        sample_thread_id: str,
    ) -> None:
        params = [
            CreateRecipeParams(
                id=f"test-recipe-id-{i}",
                user_id=sample_user_id,
                thread_id=sample_thread_id,
                created_at=datetime.now(timezone.utc) + timedelta(days=i),
                updated_at=datetime.now(timezone.utc) + timedelta(days=i + 1),
            )
            for i in range(50)
        ]

        expected_db_recipes = [
            DBRecipe(
                id=f"test-recipe-id-{i}",
                user_id=sample_user_id,
                thread_id=sample_thread_id,
                created_at=params[i].created_at.replace(tzinfo=None),
                updated_at=params[i].updated_at.replace(tzinfo=None),
                name=None,
                description=None,
                ingredients=None,
                instructions=None,
                categories=None,
                prep_time_minutes=None,
                cook_time_minutes=None,
                servings=None,
                chef_notes=None,
                substitutions=None,
                equipment_alternatives=None,
                scaling_guidance=None,
                storage_notes=None,
                serving_suggestions=None,
                make_ahead_tips=None,
                coordination_timeline=None,
            )
            for i in range(50)
        ]

        result = await recipe_service.create_recipes(async_session, params)

        assert isinstance(result, list)
        assert len(result) == 50

        for i, recipe in enumerate(result):
            assert recipe.id == params[i].id
            assert recipe.user_id == params[i].user_id
            assert recipe.thread_id == params[i].thread_id

    async def test_create_recipe(
        self,
        recipe_service: RecipeService,
        async_session: AsyncSession,
        sample_recipe: dict[str, Any],
    ) -> None:
        params = CreateRecipeParams(**sample_recipe)

        result = await recipe_service.create_recipe(async_session, params)

        assert isinstance(result, UserRecipe)

        assert result.id == params.id
        assert result.user_id == params.user_id
        assert result.thread_id == params.thread_id
        assert result.created_at == to_utc_isostring(params.created_at)
        assert result.updated_at == to_utc_isostring(params.updated_at)
        assert result.name == params.name
        assert result.description == params.description
        assert_deep_equal(result.ingredients, params.ingredients)
        assert_deep_equal(result.instructions, params.instructions)
        assert_deep_equal(result.categories, params.categories)
        assert result.prep_time_minutes == params.prep_time_minutes
        assert result.cook_time_minutes == params.cook_time_minutes
        assert result.servings == params.servings


class TestGetRecipe:
    @pytest_asyncio.fixture(scope="function")
    async def create_recipe_in_db(
        self,
        async_session: AsyncSession,
        recipe_service: RecipeService,
        sample_recipe: dict[str, Any],
    ) -> None:
        await recipe_service.create_recipe(async_session, CreateRecipeParams(**sample_recipe))
        await async_session.commit()

    @pytest_asyncio.fixture(scope="function")
    async def create_message_with_recipe_id(
        self,
        async_session: AsyncSession,
        sample_message_id: str,
        sample_recipe: dict[str, Any],
    ) -> None:
        from repositories.message_repository import MessageRepository

        message_repository = MessageRepository()
        await message_repository.create_message(
            async_session,
            CreateMessageParams(
                id=sample_message_id,
                user_id=sample_recipe["user_id"],
                thread_id=sample_recipe["thread_id"],
                role=MessageRole.user,
                content_type=MessageContentType.recipe,
                recipe_id=sample_recipe["id"],
                created_at=sample_recipe["created_at"],
                updated_at=sample_recipe["updated_at"],
            ),
        )

    async def test_get_recipe(
        self,
        recipe_service: RecipeService,
        async_session: AsyncSession,
        create_recipe_in_db: None,
        sample_recipe: dict[str, Any],
    ) -> None:
        result = await recipe_service.get_recipe(async_session, sample_recipe["id"])

        assert isinstance(result, UserRecipe)

        db_ingredients = [
            RecipeIngredient(**ingredient) for ingredient in sample_recipe["ingredients"]
        ]
        db_instructions = [
            RecipeInstruction(**instruction) for instruction in sample_recipe["instructions"]
        ]
        db_categories = [RecipeCategory(**category) for category in sample_recipe["categories"]]

        assert result.id == sample_recipe["id"]
        assert result.user_id == sample_recipe["user_id"]
        assert result.thread_id == sample_recipe["thread_id"]
        assert result.created_at == to_utc_isostring(sample_recipe["created_at"])
        assert result.updated_at == to_utc_isostring(sample_recipe["updated_at"])
        assert result.name == sample_recipe["name"]
        assert result.description == sample_recipe["description"]
        assert_deep_equal(result.ingredients, db_ingredients)
        assert_deep_equal(result.instructions, db_instructions)
        assert_deep_equal(result.categories, db_categories)
        assert result.prep_time_minutes == sample_recipe["prep_time_minutes"]
        assert result.cook_time_minutes == sample_recipe["cook_time_minutes"]
        assert result.servings == sample_recipe["servings"]

    async def test_get_non_existent_recipe(
        self, recipe_service: RecipeService, async_session: AsyncSession
    ) -> None:
        recipe_id = "test-recipe-id"

        result = await recipe_service.get_recipe(async_session, recipe_id)

        assert result is None

    async def test_get_user_recipes(
        self,
        recipe_service: RecipeService,
        async_session: AsyncSession,
        sample_recipe: dict[str, Any],
        sample_user_id: str,
        create_recipe_in_db: None,
    ) -> None:
        result = await recipe_service.get_user_recipes(async_session, sample_user_id)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == sample_recipe["id"]
        assert result[0].user_id == sample_recipe["user_id"]
        assert result[0].thread_id == sample_recipe["thread_id"]

    async def test_get_thread_recipes(
        self,
        recipe_service: RecipeService,
        async_session: AsyncSession,
        sample_recipe: dict[str, Any],
        sample_thread_id: str,
        create_recipe_in_db: None,
    ) -> None:
        result = await recipe_service.get_thread_recipes(async_session, sample_thread_id)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == sample_recipe["id"]
        assert result[0].user_id == sample_recipe["user_id"]
        assert result[0].thread_id == sample_recipe["thread_id"]

    async def test_get_recipes_by_message_id(
        self,
        recipe_service: RecipeService,
        async_session: AsyncSession,
        sample_recipe: dict[str, Any],
        sample_message_id: str,
        create_recipe_in_db: None,
        create_message_with_recipe_id: None,
    ) -> None:
        message_ids = [sample_message_id]

        result = await recipe_service.get_recipes_by_message_ids(async_session, message_ids)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == sample_recipe["id"]
        assert result[0].user_id == sample_recipe["user_id"]
        assert result[0].thread_id == sample_recipe["thread_id"]


class TestUpdateRecipe:
    @pytest_asyncio.fixture(scope="function")
    async def create_recipe_in_db(
        self,
        async_session: AsyncSession,
        recipe_service: RecipeService,
        sample_recipe: dict[str, Any],
    ) -> None:
        await recipe_service.create_recipe(
            async_session,
            CreateRecipeParams(**sample_recipe),
        )
        await async_session.commit()

    async def test_update_recipe(
        self,
        recipe_service: RecipeService,
        async_session: AsyncSession,
        create_recipe_in_db: None,
        sample_recipe: dict[str, Any],
    ) -> None:
        params = UpdateRecipeParams(
            id=sample_recipe["id"],
            updated_at=sample_recipe["updated_at"],
            name="test-name",
            description="test-description",
        )
        result = await recipe_service.update_recipe(async_session, params)
        await async_session.commit()

        assert isinstance(result, UserRecipe)

        assert result.id == sample_recipe["id"]
        assert result.user_id == sample_recipe["user_id"]
        assert result.thread_id == sample_recipe["thread_id"]
        assert result.name == "test-name"
        assert result.description == "test-description"

    async def test_update_recipe_field(
        self,
        recipe_service: RecipeService,
        async_session: AsyncSession,
        create_recipe_in_db: None,
        sample_recipe: dict[str, Any],
    ) -> None:
        params = UpdateRecipeFieldParams(
            id=sample_recipe["id"],
            updated_at=sample_recipe["updated_at"],
            field=RecipeField(
                name="name",
                value="test-name",
            ),
        )

        result = await recipe_service.update_recipe_field(async_session, params)
        await async_session.commit()

        assert isinstance(result, UserRecipe)

        assert result.id == sample_recipe["id"]
        assert result.user_id == sample_recipe["user_id"]
        assert result.thread_id == sample_recipe["thread_id"]
        assert result.name == "test-name"
