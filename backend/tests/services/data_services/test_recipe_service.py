from datetime import datetime, timezone, timedelta
from typing import cast

import pytest
import pytest_asyncio

from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from database.schema import DBRecipe

from repositories.recipe_repository import RecipeRepository

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
def mock_recipe_repository() -> RecipeRepository:
    return MagicMock(spec=RecipeRepository)


@pytest.fixture(scope="function")
def mock_async_session() -> AsyncSession:
    return MagicMock(spec=AsyncSession)


@pytest.fixture(scope="function")
def recipe_service(mock_recipe_repository: RecipeRepository) -> RecipeService:
    return RecipeService(mock_recipe_repository)


@pytest.fixture(scope="function")
def sample_recipe_id() -> str:
    return "test-recipe-id"


@pytest.fixture(scope="function")
def sample_user_id() -> str:
    return "test-user-id"


@pytest.fixture(scope="function")
def sample_thread_id() -> str:
    return "test-thread-id"


@pytest.fixture(scope="function")
def sample_mesage_id() -> str:
    return "test-message-id"


@pytest.fixture(scope="function")
def sample_timestamps() -> tuple[datetime, datetime]:
    return (datetime.now(timezone.utc), datetime.now(timezone.utc))


@pytest.fixture(scope="function")
def mock_db_recipe(sample_recipe_id: str, sample_user_id: str, sample_thread_id: str, sample_timestamps: tuple[datetime, datetime]) -> DBRecipe:
    return DBRecipe(
        id=sample_recipe_id,
        user_id=sample_user_id,
        thread_id=sample_thread_id,
        created_at=sample_timestamps[0].replace(tzinfo=None),
        updated_at=sample_timestamps[1].replace(tzinfo=None),
        name="test-name",
        description="test-description",
        ingredients=[{
            "name": "test-ingredient-name",
            "quantity": "test-ingredient-quantity",
            "unit": "test-ingredient-unit",
        }],
        instructions=[{
            "title": "test-instruction-title",
            "description": "test-instruction-description",
        }], 
        categories=[{
            "name": "test-category-name",
        }],
        prep_time_minutes=10,
        cook_time_minutes=20,
        servings="4"
    )
    

class TestRecipeService:
    async def test_create_recipe(self, recipe_service: RecipeService, mock_async_session: AsyncSession, mock_recipe_repository: RecipeRepository, mock_db_recipe: DBRecipe, sample_recipe_id: str, sample_user_id: str, sample_thread_id: str, sample_timestamps: tuple[datetime, datetime]):
        params = CreateRecipeParams(
            id=sample_recipe_id,
            user_id=sample_user_id,
            thread_id=sample_thread_id,
            created_at=sample_timestamps[0],
            updated_at=sample_timestamps[1],
            name="test-name",
            description="test-description",
            ingredients=[
                RecipeIngredient(name="test-ingredient-name", quantity="test-ingredient-quantity", unit="test-ingredient-unit"),
            ],
            instructions=[
                RecipeInstruction(title="test-instruction-title", description="test-instruction-description"),
            ],
            categories=[
                RecipeCategory(name="test-category-name"),
            ],
            prep_time_minutes=10,
            cook_time_minutes=20,
            servings="4"
        )
        
        
        mock_recipe_repository.create_recipe.return_value = mock_db_recipe
        
        result = await recipe_service.create_recipe(mock_async_session, params)
        
        assert isinstance(result, UserRecipe)
        
        assert result.id == sample_recipe_id
        assert result.user_id == sample_user_id
        assert result.thread_id == sample_thread_id
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
        
        
    async def test_get_recipe(self, recipe_service: RecipeService, mock_async_session: AsyncSession, mock_recipe_repository: RecipeRepository, mock_db_recipe: DBRecipe, sample_recipe_id: str, sample_user_id: str, sample_thread_id: str, sample_timestamps: tuple[datetime, datetime]):
        mock_recipe_repository.get_recipe.return_value = mock_db_recipe
        
        result = await recipe_service.get_recipe(mock_async_session, sample_recipe_id)
        
        assert isinstance(result, UserRecipe)
        
        mock_db_ingredients = [
            RecipeIngredient.model_validate(ingredient)
            for ingredient in cast(list[dict], mock_db_recipe.ingredients)
        ]
        mock_db_instructions = [
            RecipeInstruction.model_validate(instruction)
            for instruction in cast(list[dict], mock_db_recipe.instructions)
        ]
        mock_db_categories = [
            RecipeCategory.model_validate(category)
            for category in cast(list[dict], mock_db_recipe.categories)
        ]
        
        assert result.id == sample_recipe_id
        assert result.user_id == sample_user_id
        assert result.thread_id == sample_thread_id
        assert result.created_at == to_utc_isostring(sample_timestamps[0])
        assert result.updated_at == to_utc_isostring(sample_timestamps[1])
        assert result.name == mock_db_recipe.name
        assert result.description == mock_db_recipe.description
        assert_deep_equal(result.ingredients, mock_db_ingredients)
        assert_deep_equal(result.instructions, mock_db_instructions)
        assert_deep_equal(result.categories, mock_db_categories)
        assert result.prep_time_minutes == mock_db_recipe.prep_time_minutes
        assert result.cook_time_minutes == mock_db_recipe.cook_time_minutes
        assert result.servings == mock_db_recipe.servings
        
        
    async def test_get_non_existent_recipe(self, recipe_service: RecipeService, mock_async_session: AsyncSession, mock_recipe_repository: RecipeRepository):
        recipe_id = "test-recipe-id"
        
        mock_recipe_repository.get_recipe.return_value = None
        
        result = await recipe_service.get_recipe(mock_async_session, recipe_id)
        
        assert result is None
        
        
    async def test_get_user_recipes(self, recipe_service: RecipeService, mock_async_session: AsyncSession, mock_recipe_repository: RecipeRepository, mock_db_recipe: DBRecipe, sample_user_id: str):
        mock_recipe_repository.get_user_recipes.return_value = [mock_db_recipe]
        
        result = await recipe_service.get_user_recipes(mock_async_session, sample_user_id)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == mock_db_recipe.id
        assert result[0].user_id == sample_user_id
        assert result[0].thread_id == mock_db_recipe.thread_id
        
        
    async def test_update_recipe(self, recipe_service: RecipeService, mock_async_session: AsyncSession, mock_recipe_repository: RecipeRepository, mock_db_recipe: DBRecipe, sample_recipe_id: str, sample_user_id: str, sample_thread_id: str, sample_timestamps: tuple[datetime, datetime]):
        params = UpdateRecipeParams(
            id=sample_recipe_id,
            updated_at=sample_timestamps[1],
            name="test-name",
            description="test-description",
        )
        
        mock_recipe_repository.update_recipe.return_value = DBRecipe(   
            id=sample_recipe_id,
            user_id=sample_user_id,
            thread_id=sample_thread_id,
            created_at=sample_timestamps[0],
            updated_at=sample_timestamps[1],
            name=params.name,
            description=params.description,
            ingredients=mock_db_recipe.ingredients,
            instructions=mock_db_recipe.instructions,
            categories=mock_db_recipe.categories,
            prep_time_minutes=mock_db_recipe.prep_time_minutes,
            cook_time_minutes=mock_db_recipe.cook_time_minutes,
            servings=mock_db_recipe.servings,
            chef_notes=mock_db_recipe.chef_notes,
            substitutions=mock_db_recipe.substitutions,
            equipment_alternatives=mock_db_recipe.equipment_alternatives,
            scaling_guidance=mock_db_recipe.scaling_guidance,
            storage_notes=mock_db_recipe.storage_notes,
            serving_suggestions=mock_db_recipe.serving_suggestions,
            make_ahead_tips=mock_db_recipe.make_ahead_tips,
            coordination_timeline=mock_db_recipe.coordination_timeline,
        )
        
        result = await recipe_service.update_recipe(mock_async_session, params)
        
        assert isinstance(result, UserRecipe)
        
        assert result.id == sample_recipe_id
        assert result.user_id == sample_user_id
        assert result.thread_id == sample_thread_id
        assert result.name == "test-name"
        assert result.description == "test-description"
        
        
    async def test_update_recipe_field(self, recipe_service: RecipeService, mock_async_session: AsyncSession, mock_recipe_repository: RecipeRepository, mock_db_recipe: DBRecipe, sample_recipe_id: str, sample_user_id: str, sample_thread_id: str, sample_timestamps: tuple[datetime, datetime]):
        params = UpdateRecipeFieldParams(
            id=sample_recipe_id,
            updated_at=sample_timestamps[1],
            field=RecipeField(
                name="name",
                value="test-name",
            ),
        )
        
        mock_recipe_repository.update_recipe_field.return_value = DBRecipe(
            id=sample_recipe_id,
            user_id=sample_user_id,
            thread_id=sample_thread_id,
            created_at=sample_timestamps[0],
            updated_at=sample_timestamps[1],
            name="test-name",
            description=mock_db_recipe.description,
            ingredients=mock_db_recipe.ingredients,
            instructions=mock_db_recipe.instructions,
            categories=mock_db_recipe.categories,
            prep_time_minutes=mock_db_recipe.prep_time_minutes,
            cook_time_minutes=mock_db_recipe.cook_time_minutes,
            servings=mock_db_recipe.servings,
            chef_notes=mock_db_recipe.chef_notes,
            substitutions=mock_db_recipe.substitutions,
            equipment_alternatives=mock_db_recipe.equipment_alternatives,
            scaling_guidance=mock_db_recipe.scaling_guidance,
            storage_notes=mock_db_recipe.storage_notes,
            serving_suggestions=mock_db_recipe.serving_suggestions,
            make_ahead_tips=mock_db_recipe.make_ahead_tips,
            coordination_timeline=mock_db_recipe.coordination_timeline,
        )
        
        result = await recipe_service.update_recipe_field(mock_async_session, params)
        
        assert isinstance(result, UserRecipe)
        
        assert result.id == sample_recipe_id
        assert result.user_id == sample_user_id
        assert result.thread_id == sample_thread_id
        assert result.name == "test-name"
        
        
    async def test_get_thread_recipes(self, recipe_service: RecipeService, mock_async_session: AsyncSession, mock_recipe_repository: RecipeRepository, mock_db_recipe: DBRecipe, sample_thread_id: str):
        mock_recipe_repository.get_thread_recipes.return_value = [mock_db_recipe]
        
        result = await recipe_service.get_thread_recipes(mock_async_session, sample_thread_id)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == mock_db_recipe.id
        assert result[0].user_id == mock_db_recipe.user_id
        assert result[0].thread_id == sample_thread_id
        
    
    async def test_get_recipes_by_message_id(self, recipe_service: RecipeService, mock_async_session: AsyncSession, mock_recipe_repository: RecipeRepository, mock_db_recipe: DBRecipe, sample_mesage_id: str):
        message_ids = [sample_mesage_id]
        
        mock_recipe_repository.get_recipes_by_message_id.return_value = [mock_db_recipe]
        
        result = await recipe_service.get_recipes_by_message_id(mock_async_session, message_ids)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == mock_db_recipe.id
        assert result[0].user_id == mock_db_recipe.user_id
        assert result[0].thread_id == mock_db_recipe.thread_id
        
        
    async def test_create_recipes(self, recipe_service: RecipeService, mock_async_session: AsyncSession, mock_recipe_repository: RecipeRepository, mock_db_recipe: DBRecipe, sample_user_id: str, sample_thread_id: str):
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
        
        mock_recipe_repository.create_recipes.return_value = expected_db_recipes
        
        result = await recipe_service.create_recipes(mock_async_session, params)
        
        assert isinstance(result, list)
        assert len(result) == 50
        
        for i, recipe in enumerate(result):
            assert recipe.id == params[i].id
            assert recipe.user_id == params[i].user_id
            assert recipe.thread_id == params[i].thread_id