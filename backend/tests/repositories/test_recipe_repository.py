import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.message_repository import MessageRepository
from repositories.recipe_repository import RecipeRepository

from schemas.messages import CreateMessageParams
from schemas.message_content_type import MessageContentType
from schemas.message_role import MessageRole
from schemas.recipes import (
    RecipeField,
    RecipeCategory,
    RecipeIngredient,
    RecipeInstruction,
    CreateRecipeParams,
    UpdateRecipeFieldParams,
    UpdateRecipeParams,
)

from utils.date_utils import strip_timezone

from tests.utils.assert_deep_equal import assert_deep_equal


pytestmark = pytest.mark.asyncio

@pytest.fixture 
def recipe_repository():
    return RecipeRepository()


@pytest.fixture
def recipe_id():
    return str(uuid4())


@pytest.fixture
def user_id():
    return str(uuid4())


@pytest.fixture
def thread_id():
    return str(uuid4())


@pytest.fixture
def sample_recipe(recipe_id: str, user_id: str, thread_id: str):
    """Create a sample recipe with all required fields for testing."""
    return {
        "id": recipe_id,
        "user_id": user_id,
        "thread_id": thread_id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "name": "Test Recipe",
        "description": "Test Description",
        "ingredients": [RecipeIngredient(name="Test Ingredient", quantity="1", unit="unit")],
        "instructions": [RecipeInstruction(title="Test Instruction", description="Test Description")],
        "categories": [RecipeCategory(name="Test Category")],
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "servings": "4",
        "chef_notes": "Test Chef Notes",
        "substitutions": "Test Substitutions",
        "equipment_alternatives": "Test Equipment Alternatives",
        "scaling_guidance": "Test Scaling Guidance",
        "storage_notes": "Test Storage Notes",
        "serving_suggestions": "Test Serving Suggestions",
        "make_ahead_tips": "Test Make Ahead Tips",
        "coordination_timeline": "Test Coordination Timeline",
    }
    

class TestCreateRecipe:
    async def test_create_recipe(self, async_session: AsyncSession, recipe_repository: RecipeRepository, sample_recipe: dict):
        """Test creating a recipe with all fields and verifying storage."""
        params = CreateRecipeParams(**sample_recipe)
        
        await recipe_repository.create_recipe(async_session, params)
        await async_session.commit()
        
        recipe = await recipe_repository.get_recipe(async_session, params.id)
        assert recipe is not None
        assert_deep_equal(recipe.name, params.name)
        assert_deep_equal(recipe.description, params.description)
        
        assert isinstance(recipe.ingredients[0], dict)
        assert isinstance(recipe.instructions[0], dict)
        assert isinstance(recipe.categories[0], dict)
        
        recipe_ingredients = [RecipeIngredient(**ing) for ing in recipe.ingredients]
        assert_deep_equal(recipe_ingredients, params.ingredients)
        
        recipe_instructions = [RecipeInstruction(**inst) for inst in recipe.instructions]
        assert_deep_equal(recipe_instructions, params.instructions)
        
        recipe_categories = [RecipeCategory(**cat) for cat in recipe.categories]
        assert_deep_equal(recipe_categories, params.categories)
        
        assert_deep_equal(recipe.prep_time_minutes, params.prep_time_minutes)
        assert_deep_equal(recipe.cook_time_minutes, params.cook_time_minutes)
        assert_deep_equal(recipe.servings, params.servings)
        assert_deep_equal(recipe.chef_notes, params.chef_notes)
        assert_deep_equal(recipe.substitutions, params.substitutions)
        assert_deep_equal(recipe.equipment_alternatives, params.equipment_alternatives)
        assert_deep_equal(recipe.scaling_guidance, params.scaling_guidance)
        assert_deep_equal(recipe.storage_notes, params.storage_notes)
        assert_deep_equal(recipe.serving_suggestions, params.serving_suggestions)
        assert_deep_equal(recipe.make_ahead_tips, params.make_ahead_tips)
        assert_deep_equal(recipe.coordination_timeline, params.coordination_timeline)
        
        
class TestGetRecipe:
    @pytest_asyncio.fixture(scope="function")
    async def create_recipe_in_db(self, async_session: AsyncSession, recipe_repository: RecipeRepository, sample_recipe: dict):
        params = CreateRecipeParams(**sample_recipe)
        await recipe_repository.create_recipe(async_session, params)
        await async_session.commit()
        
        
    async def test_get_recipe(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_recipe_in_db, recipe_id: str, sample_recipe: dict):
        """Test retrieving a recipe by ID and verifying all fields match."""
        recipe = await recipe_repository.get_recipe(async_session, recipe_id)
        assert recipe is not None
        
        assert_deep_equal(recipe.id, recipe_id)
        assert_deep_equal(recipe.user_id, sample_recipe["user_id"])
        assert_deep_equal(recipe.thread_id, sample_recipe["thread_id"])
        assert_deep_equal(recipe.created_at, strip_timezone(sample_recipe["created_at"]))
        assert_deep_equal(recipe.updated_at, strip_timezone(sample_recipe["updated_at"]))
        
        assert_deep_equal(recipe.name, sample_recipe["name"])
        assert_deep_equal(recipe.description, sample_recipe["description"])
        
        assert isinstance(recipe.ingredients[0], dict)
        assert isinstance(recipe.instructions[0], dict)
        assert isinstance(recipe.categories[0], dict)
        
        recipe_ingredients = [RecipeIngredient(**ing) for ing in recipe.ingredients]
        assert_deep_equal(recipe_ingredients, sample_recipe["ingredients"])
        
        recipe_instructions = [RecipeInstruction(**inst) for inst in recipe.instructions]
        assert_deep_equal(recipe_instructions, sample_recipe["instructions"])
        
        recipe_categories = [RecipeCategory(**cat) for cat in recipe.categories]
        assert_deep_equal(recipe_categories, sample_recipe["categories"])
        
        assert_deep_equal(recipe.name, sample_recipe["name"])
        assert_deep_equal(recipe.description, sample_recipe["description"])
        assert_deep_equal(recipe.prep_time_minutes, sample_recipe["prep_time_minutes"])
        assert_deep_equal(recipe.cook_time_minutes, sample_recipe["cook_time_minutes"])
        assert_deep_equal(recipe.servings, sample_recipe["servings"])
        assert_deep_equal(recipe.chef_notes, sample_recipe["chef_notes"])
        assert_deep_equal(recipe.substitutions, sample_recipe["substitutions"])
        assert_deep_equal(recipe.equipment_alternatives, sample_recipe["equipment_alternatives"])
        assert_deep_equal(recipe.scaling_guidance, sample_recipe["scaling_guidance"])
        assert_deep_equal(recipe.storage_notes, sample_recipe["storage_notes"])
        assert_deep_equal(recipe.serving_suggestions, sample_recipe["serving_suggestions"])
        assert_deep_equal(recipe.make_ahead_tips, sample_recipe["make_ahead_tips"])
        assert_deep_equal(recipe.coordination_timeline, sample_recipe["coordination_timeline"])
        
    
    async def test_get_non_existent_recipe(self, async_session: AsyncSession, recipe_repository: RecipeRepository):
        """Test retrieving a non-existing recipe returns None."""
        recipe = await recipe_repository.get_recipe(async_session, "non-existing-recipe-id")
        assert recipe is None
        
        
class TestGetUserRecipes:
    @pytest_asyncio.fixture(scope="function")
    async def create_recipes_in_db(self, async_session: AsyncSession, recipe_repository: RecipeRepository, sample_recipe: dict):
        params = CreateRecipeParams(**sample_recipe)
        await recipe_repository.create_recipe(async_session, params)
        await async_session.commit()
        
        
    async def test_get_user_recipes(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_recipes_in_db, user_id: str, sample_recipe: dict):
        """Test retrieving all recipes for a specific user."""
        recipes = await recipe_repository.get_user_recipes(async_session, user_id)
        
        assert len(recipes) == 1
        
        assert recipes[0].id == sample_recipe["id"]
        assert recipes[0].user_id == user_id
        assert recipes[0].thread_id == sample_recipe["thread_id"]
        
        
    async def test_get_non_existent_user_recipes(self, async_session: AsyncSession, recipe_repository: RecipeRepository):
        """Test retrieving recipes for non-existing user returns empty list."""
        recipes = await recipe_repository.get_user_recipes(async_session, "non-existing-user-id")
        assert len(recipes) == 0
        
        
class TestUpdateRecipe:
    @pytest_asyncio.fixture(scope="function")
    async def create_recipe_in_db(self, async_session: AsyncSession, recipe_repository: RecipeRepository, sample_recipe: dict):
        params = CreateRecipeParams(**sample_recipe)
        await recipe_repository.create_recipe(async_session, params)
        await async_session.commit()
        
        
    async def test_update_recipe(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_recipe_in_db, sample_recipe: dict, recipe_id: str): 
        """Test updating a recipe with new values and verifying the changes."""
        params = UpdateRecipeParams(
            id=recipe_id,
            updated_at=datetime.now(timezone.utc),
            name="Updated Recipe",
            description="Updated Description",
            ingredients=[sample_recipe["ingredients"][0], RecipeIngredient(name="Updated Ingredient", quantity="2", unit="unit")],
            instructions=[sample_recipe["instructions"][0], RecipeInstruction(title="Updated Instruction", description="Updated Description")],
            categories=[sample_recipe["categories"][0], RecipeCategory(name="Updated Category")],
            prep_time_minutes=sample_recipe["prep_time_minutes"] + 10,
            cook_time_minutes=sample_recipe["cook_time_minutes"] + 10,
            servings="5",
        )
        
        
        await recipe_repository.update_recipe(async_session, params)
        await async_session.commit()
        
        recipe = await recipe_repository.get_recipe(async_session, recipe_id)
        assert recipe is not None
        
        assert_deep_equal(recipe.name, params.name)
        assert_deep_equal(recipe.description, params.description)
        
        assert len(recipe.ingredients) == 2
        assert len(recipe.instructions) == 2
        assert len(recipe.categories) == 2
        
        ingredients = [RecipeIngredient(**ing) for ing in recipe.ingredients]
        assert_deep_equal(ingredients, params.ingredients)
        
        instructions = [RecipeInstruction(**inst) for inst in recipe.instructions]
        assert_deep_equal(instructions, params.instructions)
        
        categories = [RecipeCategory(**cat) for cat in recipe.categories]
        assert_deep_equal(categories, params.categories)
        
        assert_deep_equal(recipe.prep_time_minutes, 20)
        assert_deep_equal(recipe.cook_time_minutes, 30)
        assert_deep_equal(recipe.servings, "5")
        
        
    async def test_update_recipe_with_none_values(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_recipe_in_db, sample_recipe: dict, recipe_id: str):
        """Test that updating with None values doesn't overwrite existing data."""
        params = UpdateRecipeParams(
            id=recipe_id,
            updated_at=datetime.now(timezone.utc),
            name=None,
            description=None,
        )
        
        await recipe_repository.update_recipe(async_session, params)
        await async_session.commit()
        
        recipe = await recipe_repository.get_recipe(async_session, recipe_id)
        assert recipe is not None
        assert recipe.name is not None
        assert recipe.description is not None
        
        
    async def test_update_non_existent_recipe(self, async_session: AsyncSession, recipe_repository: RecipeRepository):
        """Test updating a non-existing recipe raises ValueError."""
        params = UpdateRecipeParams(
            id="non-existing-recipe-id",
            updated_at=datetime.now(timezone.utc),
        )
        
        with pytest.raises(ValueError):
            await recipe_repository.update_recipe(async_session, params)
            
            
    async def test_update_recipe_complex_fields(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_recipe_in_db, sample_recipe: dict, recipe_id: str):
        """Test updating a recipe with complex JSON fields."""
        
        new_ingredients = [RecipeIngredient(name="Updated Ingredient", quantity="2", unit="unit"), RecipeIngredient(name="Updated Ingredient 2", quantity="3", unit="unit")]
        params = UpdateRecipeParams(
            id=recipe_id,
            updated_at=datetime.now(timezone.utc),
            ingredients=new_ingredients,
        )
        
        
        await recipe_repository.update_recipe(async_session, params)
        await async_session.commit()
        
        recipe = await recipe_repository.get_recipe(async_session, recipe_id)
        assert recipe is not None
        
        recipe_ingredients = [RecipeIngredient(**ing) for ing in recipe.ingredients]
        assert_deep_equal(recipe_ingredients, new_ingredients)
        
        
class TestUpdateRecipeField:
    @pytest_asyncio.fixture(scope="function")
    async def create_recipe_in_db(self, async_session: AsyncSession, recipe_repository: RecipeRepository, sample_recipe: dict):
        params = CreateRecipeParams(**sample_recipe)
        await recipe_repository.create_recipe(async_session, params)
        await async_session.commit()
        
        
    async def test_update_recipe_simple_string_field(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_recipe_in_db, sample_recipe: dict, recipe_id: str):       
        """Test updating a single string field of a recipe."""
        params = UpdateRecipeFieldParams(
            id=recipe_id,
            updated_at=datetime.now(timezone.utc),
            field=RecipeField(
                name="name",
                value="Updated Recipe",
            ),
        )
        
        await recipe_repository.update_recipe_field(async_session, params)
        await async_session.commit()
        
        recipe = await recipe_repository.get_recipe(async_session, recipe_id)
        assert recipe is not None
        assert_deep_equal(recipe.name, "Updated Recipe")
        
        
    async def test_update_recipe_simple_integer_field(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_recipe_in_db, sample_recipe: dict, recipe_id: str):
        """Test updating a single integer field of a recipe."""
        params = UpdateRecipeFieldParams(
            id=recipe_id,
            updated_at=datetime.now(timezone.utc),
            field=RecipeField(
                name="prep_time_minutes",
                value=123,
            ),
        )
        
        await recipe_repository.update_recipe_field(async_session, params)
        await async_session.commit()
        
        recipe = await recipe_repository.get_recipe(async_session, recipe_id)
        assert recipe is not None
        assert_deep_equal(recipe.prep_time_minutes, 123)
        
        
    async def test_update_invalid_field_payload(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_recipe_in_db, sample_recipe: dict, recipe_id: str):
        """Test updating a field with wrong type raises ValueError."""
        with pytest.raises(ValueError):
            params = UpdateRecipeFieldParams(
                id=recipe_id,
                updated_at=datetime.now(timezone.utc),
                field=RecipeField(
                    name="name",
                    value=123,  
                ),
            )
            
        with pytest.raises(ValueError):
            params = UpdateRecipeFieldParams(
                id=recipe_id,
                updated_at=datetime.now(timezone.utc),
                field=RecipeField(
                    name="prep_time_minutes",
                    value="not an integer",
                ),
            )
            
        with pytest.raises(ValueError):
            params = UpdateRecipeFieldParams(
                id=recipe_id,
                updated_at=datetime.now(timezone.utc),
                field=RecipeField(
                    name="ingredients",
                    value=RecipeIngredient(name="Updated Ingredient", quantity="2", unit="unit"),
                ),
            )
            
        
        with pytest.raises(ValueError):
            params = UpdateRecipeFieldParams(
                id=recipe_id,
                updated_at=datetime.now(timezone.utc),
                field=RecipeField(
                    name="ingredient",
                    value=[RecipeIngredient(name="Updated Ingredient", quantity="2", unit="unit")],
                ),
            )
            
        
    async def test_update_recipe_field_with_non_existent_recipe(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_recipe_in_db, sample_recipe: dict, recipe_id: str):
        """Test updating field of non-existing recipe raises ValueError."""
        params = UpdateRecipeFieldParams(
            id="non-existing-recipe-id",
            updated_at=datetime.now(timezone.utc),
            field=RecipeField(
                name="name",
                value="Updated Recipe",
            ),
        )
        
        with pytest.raises(ValueError):
            await recipe_repository.update_recipe_field(async_session, params)
        
        
    async def test_add_ingredient_to_recipe(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_recipe_in_db, sample_recipe: dict, recipe_id: str):
        """Test adding an ingredient to a recipe."""
        params = UpdateRecipeFieldParams(
            id=recipe_id,
            updated_at=datetime.now(timezone.utc),
            field=RecipeField(
                name="ingredient",
                value=RecipeIngredient(name="Updated Ingredient", quantity="2", unit="unit"),
            ),
        )
        
        await recipe_repository.update_recipe_field(async_session, params)
        await async_session.commit()
        
        recipe = await recipe_repository.get_recipe(async_session, recipe_id)
        assert recipe is not None
        
        assert isinstance(recipe.ingredients, list)
        assert len(recipe.ingredients) == 2
        
        recipe_ingredients = [RecipeIngredient(**ing) for ing in recipe.ingredients]    
        assert_deep_equal(recipe_ingredients, [sample_recipe["ingredients"][0], RecipeIngredient(name="Updated Ingredient", quantity="2", unit="unit")])
    
    
    async def test_override_recipe_ingredients(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_recipe_in_db, sample_recipe: dict, recipe_id: str):
        """Test overriding the recipe ingredients."""
        expected_ingredients = [RecipeIngredient(name="Updated Ingredient", quantity="2", unit="unit"), RecipeIngredient(name="Updated Ingredient 2", quantity="3", unit="unit"), RecipeIngredient(name="Updated Ingredient 3", quantity="4", unit="unit")]
        
        params = UpdateRecipeFieldParams(
            id=recipe_id,
            updated_at=datetime.now(timezone.utc),
            field=RecipeField(
                name="ingredients",
                value=expected_ingredients,
            ),
        )
        
        await recipe_repository.update_recipe_field(async_session, params)
        await async_session.commit()
        
        recipe = await recipe_repository.get_recipe(async_session, recipe_id)
        assert recipe is not None
        
        assert isinstance(recipe.ingredients, list)
        assert len(recipe.ingredients) == 3
        
        recipe_ingredients = [RecipeIngredient(**ing) for ing in recipe.ingredients]
        assert_deep_equal(recipe_ingredients, expected_ingredients)


        
class TestGetThreadRecipes:
    @pytest_asyncio.fixture(scope="function")
    async def create_recipes_in_db(self, async_session: AsyncSession, recipe_repository: RecipeRepository, sample_recipe: dict):
        params = CreateRecipeParams(**sample_recipe)
        await recipe_repository.create_recipe(async_session, params)
        await async_session.commit()
        
        
    async def test_get_thread_recipes(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_recipes_in_db, thread_id: str, sample_recipe: dict):       
        """Test retrieving all recipes for a specific thread."""
        recipes = await recipe_repository.get_thread_recipes(async_session, thread_id)
        assert len(recipes) == 1
        
        assert recipes[0].id == sample_recipe["id"]
        assert recipes[0].user_id == sample_recipe["user_id"]
        assert recipes[0].thread_id == thread_id
        
        
    async def test_get_thread_recipes_with_non_existent_thread(self, async_session: AsyncSession, recipe_repository: RecipeRepository):
        """Test retrieving recipes for non-existing thread returns empty list."""
        recipes = await recipe_repository.get_thread_recipes(async_session, "non-existing-thread-id")
        assert len(recipes) == 0
        
        
class TestGetRecipesByMessageId:
    @pytest.fixture(scope="function")
    def message_id(self):
        return str(uuid4())
    
    @pytest.fixture(scope="function")
    def sample_message(self, message_id: str, thread_id: str, recipe_id: str, user_id: str):
        """Sample message that references a recipe for testing."""
        return {
            "id": message_id,
            "thread_id": thread_id,
            "user_id": user_id,
            "role": MessageRole.assistant,
            "content_type": MessageContentType.recipe,
            "recipe_id": recipe_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    
    @pytest_asyncio.fixture(scope="function")
    async def create_message_in_db(self, async_session: AsyncSession, sample_message: dict):
        message_repository = MessageRepository()
        params = CreateMessageParams(**sample_message)
        await message_repository.create_message(async_session, params)
        await async_session.commit()
        
    @pytest_asyncio.fixture(scope="function")
    async def create_recipes_in_db(self, async_session: AsyncSession, recipe_repository: RecipeRepository, sample_recipe: dict):
        params = CreateRecipeParams(**sample_recipe)
        await recipe_repository.create_recipe(async_session, params)
        await async_session.commit()
        
        
    async def test_get_recipes_by_message_id(self, async_session: AsyncSession, recipe_repository: RecipeRepository, create_message_in_db, create_recipes_in_db, sample_message: dict, sample_recipe: dict, message_id: str, recipe_id: str):
        """Test retrieving recipes by message id."""
        recipes = await recipe_repository.get_recipes_by_message_id(async_session, [message_id])
        assert len(recipes) == 1
        
        assert recipes[0].id == recipe_id
        assert recipes[0].user_id == sample_recipe["user_id"]
        assert recipes[0].thread_id == sample_recipe["thread_id"]
        
        
class TestCreateRecipes:
    @pytest_asyncio.fixture(scope="function")
    async def create_batch_recipes_in_db(self, async_session: AsyncSession, recipe_repository: RecipeRepository, sample_recipe: dict):
        params = [CreateRecipeParams(**sample_recipe) for _ in range(10)]
        await recipe_repository.create_recipes(async_session, params)
        await async_session.commit()
        
        assert len(params) == 10
        