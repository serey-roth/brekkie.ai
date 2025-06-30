from datetime import datetime, timezone
import asyncio

import pytest
import pytest_asyncio

from fakeredis.aioredis import FakeRedis

from services.data_services.recipe_cache_service import RecipeCacheService
    
from schemas.recipes import (
    CreateRecipeParams,
    UpdateRecipeFieldParams,
    UpdateRecipeParams,
    UserRecipe,
    RecipeField,
    RecipeIngredient,
    RecipeInstruction,
    RecipeCategory
)

from utils.date_utils import to_utc_isostring

from tests.utils.assert_deep_equal import assert_deep_equal


@pytest_asyncio.fixture
async def recipe_cache_service(redis_client: FakeRedis) -> RecipeCacheService:
    await redis_client.flushall()
    return RecipeCacheService(redis_client, ttl=30) # 30 seconds for testing


@pytest.fixture
def user_id() -> str:
    return "user_id"


@pytest.fixture
def thread_id() -> str:
    return "thread_id"


@pytest.fixture
def recipe_id() -> str:
    return "recipe_id"


@pytest.fixture
def sample_recipe(user_id: str, thread_id: str, recipe_id: str) -> UserRecipe:
    return UserRecipe(
        id=recipe_id,
        user_id=user_id,
        thread_id=thread_id,
        created_at=to_utc_isostring(datetime.now(timezone.utc)),
        updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        name="recipe_name",
        description="recipe description",
        ingredients=[RecipeIngredient(
            name="ingredient_name",
            quantity="1",
            unit="unit"
        )],
        instructions=[RecipeInstruction(
            title="instruction_title",
            description="instruction_description"
        )],
        categories=[RecipeCategory(
            name="category_name"
        )],
        prep_time_minutes=10,
        cook_time_minutes=10,
        servings="1",
    )
    

class TestBasicRecipeOperations:
    def test_get_recipe_key(self, recipe_cache_service: RecipeCacheService):
        key = recipe_cache_service._get_recipe_key("user_id", "thread_id", "recipe_id")
        assert key == "brekkie:chat_session:user_id:threads:thread_id:recipes:recipe_id"
        

    def test_get_all_recipes_key(self, recipe_cache_service: RecipeCacheService):
        key = recipe_cache_service._get_all_recipes_key("user_id", "thread_id")
        assert key == "brekkie:chat_session:user_id:threads:thread_id:recipes:*"
        
        
    def test_get_all_user_recipes_key(self, recipe_cache_service: RecipeCacheService):
        key = recipe_cache_service._get_all_user_recipes_key("user_id")
        assert key == "brekkie:chat_session:user_id:threads:*:recipes:*"


    @pytest.mark.asyncio
    async def test_set_and_get_recipe(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(sample_recipe)
        recipe = await recipe_cache_service.get_recipe(user_id, thread_id, recipe_id)
        assert_deep_equal(recipe, sample_recipe)
        
        
    @pytest.mark.asyncio
    async def test_set_and_get_recipe_with_ttl(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(sample_recipe, ttl=1)
        recipe = await recipe_cache_service.get_recipe(user_id, thread_id, recipe_id)
        assert_deep_equal(recipe, sample_recipe)
        await asyncio.sleep(1.5)
        recipe = await recipe_cache_service.get_recipe(user_id, thread_id, recipe_id)
        assert recipe is None
        
        
    @pytest.mark.asyncio
    async def test_get_recipes(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(sample_recipe)
        recipes = await recipe_cache_service.get_recipes(user_id, thread_id)
        assert_deep_equal(recipes, [sample_recipe])
        
        
    @pytest.mark.asyncio
    async def test_get_recipes_by_ids(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(sample_recipe)
        
        recipes = await recipe_cache_service.get_recipes_by_ids(user_id, thread_id, [recipe_id])
        assert_deep_equal(recipes, [sample_recipe])
        
        
    @pytest.mark.asyncio
    async def test_create_recipe_with_no_recipe_fields(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        params = CreateRecipeParams(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at=created_at,
            updated_at=updated_at,
        )
        
        recipe = await recipe_cache_service.create_recipe(params)
        assert_deep_equal(recipe, UserRecipe(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at=to_utc_isostring(created_at),
            updated_at=to_utc_isostring(updated_at),
        ))
        
        assert recipe.name is None
        assert recipe.description is None
        assert recipe.ingredients is None
        assert recipe.instructions is None
        assert recipe.categories is None
        assert recipe.prep_time_minutes is None
        assert recipe.cook_time_minutes is None
        assert recipe.servings is None
        assert recipe.chef_notes is None
        assert recipe.substitutions is None
        assert recipe.equipment_alternatives is None
        assert recipe.scaling_guidance is None
        assert recipe.storage_notes is None
        
        
    @pytest.mark.asyncio
    async def test_create_recipe_with_recipe_fields(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        params = CreateRecipeParams(
            created_at=datetime.fromisoformat(sample_recipe.created_at),
            updated_at=datetime.fromisoformat(sample_recipe.updated_at),
            **sample_recipe.model_dump(exclude={"created_at", "updated_at"}),
        )
        recipe = await recipe_cache_service.create_recipe(params)
        assert_deep_equal(recipe, sample_recipe)
        
    
    @pytest.mark.asyncio
    async def test_create_recipe_with_ttl(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        params = CreateRecipeParams(
            created_at=datetime.fromisoformat(sample_recipe.created_at),
            updated_at=datetime.fromisoformat(sample_recipe.updated_at),
            **sample_recipe.model_dump(exclude={"created_at", "updated_at"}),
        )
        recipe = await recipe_cache_service.create_recipe(params, ttl=1)
        assert_deep_equal(recipe, sample_recipe)    
        
        await asyncio.sleep(1.5)
        recipe = await recipe_cache_service.get_recipe(user_id, thread_id, recipe_id)
        assert recipe is None
        
        
    @pytest.mark.asyncio
    async def test_get_recipes_by_user_id(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str):
        first_recipe = sample_recipe.model_copy(update={"id": "first_recipe_id", "thread_id": "first_thread_id"})
        second_recipe = sample_recipe.model_copy(update={"id": "second_recipe_id", "thread_id": "second_thread_id"})
        third_recipe = sample_recipe.model_copy(update={"id": "third_recipe_id", "thread_id": "third_thread_id"})
        
        await recipe_cache_service.set_recipe(first_recipe)
        await recipe_cache_service.set_recipe(second_recipe)
        await recipe_cache_service.set_recipe(third_recipe)
        
        recipes = await recipe_cache_service.get_recipes_by_user_id(user_id)
        assert_deep_equal(recipes, [first_recipe, second_recipe, third_recipe])
        
        
    @pytest.mark.asyncio
    async def test_delete_recipes_by_user_id(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str):
        first_recipe = sample_recipe.model_copy(update={"id": "first_recipe_id", "thread_id": "first_thread_id"})
        second_recipe = sample_recipe.model_copy(update={"id": "second_recipe_id", "thread_id": "second_thread_id"})
        third_recipe = sample_recipe.model_copy(update={"id": "third_recipe_id", "thread_id": "third_thread_id"})
        
        await recipe_cache_service.set_recipe(first_recipe)
        await recipe_cache_service.set_recipe(second_recipe)
        await recipe_cache_service.set_recipe(third_recipe)
        
        await recipe_cache_service.delete_recipes_by_user_id(user_id)
        recipes = await recipe_cache_service.get_recipes_by_user_id(user_id)
        assert len(recipes) == 0
        
        
class TestUpdateRecipeField:
    @pytest.mark.asyncio
    async def test_update_recipe_simple_field(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(sample_recipe)
        
        updated_at = datetime.now(timezone.utc)
        
        params = UpdateRecipeFieldParams(
            id=recipe_id,
            field=RecipeField(
                name="name",
                value="new_name",
            ),
            updated_at=updated_at,
        )
        
        recipe = await recipe_cache_service.update_recipe_field(user_id, thread_id, params)
        assert_deep_equal(recipe, sample_recipe.model_copy(update={"name": "new_name", "updated_at": to_utc_isostring(updated_at)}))
        
        
    @pytest.mark.asyncio
    async def test_add_first_ingredient(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(UserRecipe(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        ))
        
        updated_at = datetime.now(timezone.utc)
        
        first_ingredient = RecipeIngredient(
            name="new_ingredient_name",
            quantity="1",
            unit="unit"
        )
        
        params = UpdateRecipeFieldParams(
            id=recipe_id,
            field=RecipeField(
                name="ingredient",
                value=first_ingredient,
            ),
            updated_at=updated_at,
        )
        
        recipe = await recipe_cache_service.update_recipe_field(user_id, thread_id, params) 
    
        assert len(recipe.ingredients) == 1
        assert isinstance(recipe.ingredients[0], RecipeIngredient)
        assert_deep_equal(recipe.ingredients[0], first_ingredient)
        
    
    @pytest.mark.asyncio
    async def test_add_second_ingredient(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(UserRecipe(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            ingredients=[RecipeIngredient(
                name="first_ingredient_name",
                quantity="1",
                unit="unit"
            )],
        ))
        
        second_ingredient = RecipeIngredient(
            name="second_ingredient_name",
            quantity="2",
            unit="unit"
        )
        
        updated_at = datetime.now(timezone.utc)
        
        params = UpdateRecipeFieldParams(
            id=recipe_id,
            field=RecipeField(
                name="ingredient",
                value=second_ingredient,
            ),
            updated_at=updated_at,
        )
        
        recipe = await recipe_cache_service.update_recipe_field(user_id, thread_id, params)
        assert len(recipe.ingredients) == 2
        assert_deep_equal(recipe.ingredients[1], second_ingredient)
        

    @pytest.mark.asyncio
    async def test_add_instruction(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(UserRecipe(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            instructions=[],
        ))
        
        updated_at = datetime.now(timezone.utc)
        
        first_instruction = RecipeInstruction(
            title="first_instruction_title",
            description="first_instruction_description"
        )
        
        params = UpdateRecipeFieldParams(
            id=recipe_id,
            field=RecipeField(
                name="instruction",
                value=first_instruction,
            ),
            updated_at=updated_at,
        )
        
        recipe = await recipe_cache_service.update_recipe_field(user_id, thread_id, params)
        assert len(recipe.instructions) == 1
        assert_deep_equal(recipe.instructions[0], first_instruction)
        
        
    @pytest.mark.asyncio
    async def test_add_category(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(UserRecipe(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        ))
        
        updated_at = datetime.now(timezone.utc)
        
        first_category = RecipeCategory(
            name="first_category_name"
        )
        
        params = UpdateRecipeFieldParams(
            id=recipe_id,
            field=RecipeField(
                name="category",
                value=first_category,
            ),
            updated_at=updated_at,
        )
        
        recipe = await recipe_cache_service.update_recipe_field(user_id, thread_id, params)
        assert len(recipe.categories) == 1
        assert_deep_equal(recipe.categories[0], first_category)
        
        
    @pytest.mark.asyncio
    async def test_update_non_existent_recipe(self, recipe_cache_service: RecipeCacheService, user_id: str, thread_id: str, recipe_id: str):
        params = UpdateRecipeFieldParams(
            id=recipe_id,
            field=RecipeField(
                name="name",
                value="new_name",
            ),
            updated_at=datetime.now(timezone.utc),
        )
        
        with pytest.raises(ValueError):
            await recipe_cache_service.update_recipe_field(user_id, thread_id, params)
            
            
    @pytest.mark.asyncio
    async def test_update_recipe_with_invalid_field_value(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(sample_recipe)
        
        with pytest.raises(ValueError):
            await recipe_cache_service.update_recipe_field(user_id, thread_id, UpdateRecipeFieldParams(
                id=recipe_id,
                field=RecipeField(
                    name="name",
                    value=1,
                ),
                updated_at=datetime.now(timezone.utc),
            ))
            
        with pytest.raises(ValueError):
            await recipe_cache_service.update_recipe_field(user_id, thread_id, UpdateRecipeFieldParams(
                id=recipe_id,
                field=RecipeField(
                    name="ingredients",
                    value=1,
                ),
                updated_at=datetime.now(timezone.utc),
            ))
            
            
        with pytest.raises(ValueError):
            await recipe_cache_service.update_recipe_field(user_id, thread_id, UpdateRecipeFieldParams(
                id=recipe_id,
                field=RecipeField(
                    name="ingredient",
                    value=[],
                ),
                updated_at=datetime.now(timezone.utc),
            ))
            

class TestUpdateRecipe:
    @pytest.mark.asyncio
    async def test_update_recipe(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(sample_recipe)
        
        updated_at = datetime.now(timezone.utc)
        
        params = UpdateRecipeParams(
            id=recipe_id,
            name="new_name",
            updated_at=updated_at,
        )
        
        recipe = await recipe_cache_service.update_recipe(user_id, thread_id, params)
        assert_deep_equal(recipe, sample_recipe.model_copy(update={"name": "new_name", "updated_at": to_utc_isostring(updated_at)}))
            
        
    @pytest.mark.asyncio
    async def test_update_recipe_with_invalid_field_value(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(sample_recipe)
        
        with pytest.raises(ValueError):
            await recipe_cache_service.update_recipe(user_id, thread_id, UpdateRecipeParams(
                id=recipe_id,
                name=1,
                updated_at=datetime.now(timezone.utc),
            ))
            
            
    
    @pytest.mark.asyncio
    async def test_update_recipe_with_ingredients(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(sample_recipe)
        
        updated_at = datetime.now(timezone.utc)
        
        new_ingredient = RecipeIngredient(      
            name="new_ingredient_name",
            quantity="1",
            unit="unit"
        )
        
        params = UpdateRecipeParams(
            id=recipe_id,
            ingredients=[new_ingredient],
            updated_at=updated_at,
        )
        
        recipe = await recipe_cache_service.update_recipe(user_id, thread_id, params)
        assert len(recipe.ingredients) == 1
        assert_deep_equal(recipe.ingredients[0], new_ingredient)
        
        
    @pytest.mark.asyncio
    async def test_update_recipe_with_instructions(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(sample_recipe)
        
        updated_at = datetime.now(timezone.utc)
        
        new_instruction = RecipeInstruction(
            title="new_instruction_title",
            description="new_instruction_description"
        )
        
        params = UpdateRecipeParams(
            id=recipe_id,
            instructions=[new_instruction],
            updated_at=updated_at,
        )
        
        recipe = await recipe_cache_service.update_recipe(user_id, thread_id, params)
        assert len(recipe.instructions) == 1
        assert_deep_equal(recipe.instructions[0], new_instruction)
        
        
    @pytest.mark.asyncio
    async def test_update_recipe_with_categories(self, recipe_cache_service: RecipeCacheService, sample_recipe: UserRecipe, user_id: str, thread_id: str, recipe_id: str):
        await recipe_cache_service.set_recipe(sample_recipe)
        
        updated_at = datetime.now(timezone.utc)
        
        new_category = RecipeCategory(
            name="new_category_name"
        )       
        
        params = UpdateRecipeParams(
            id=recipe_id,
            categories=[new_category],
            updated_at=updated_at,
        )
        
        recipe = await recipe_cache_service.update_recipe(user_id, thread_id, params)
        assert len(recipe.categories) == 1
        assert_deep_equal(recipe.categories[0], new_category)   