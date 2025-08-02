from datetime import datetime
from typing import cast

from database.schema import DBRecipe
from repositories.recipe_repository import RecipeRepository
from schemas.recipes import (
    CreateRecipeParams,
    Recipe,
    RecipeCategory,
    RecipeField,
    RecipeIngredient,
    RecipeInstruction,
    UpdateRecipeFieldParams,
    UpdateRecipeParams,
    UserRecipe,
)
from sqlalchemy.ext.asyncio import AsyncSession
from utils.date_utils import to_utc_isostring
from utils.logger import Logger

logger = Logger("recipe_service")


class RecipeService:
    def __init__(self, repository: RecipeRepository):
        self.repository = repository

    def _to_user_recipe_dto(self, recipe: DBRecipe) -> UserRecipe:
        return UserRecipe(
            id=str(recipe.id),
            user_id=str(recipe.user_id),
            thread_id=str(recipe.thread_id),
            name=str(recipe.name) if recipe.name is not None else None,
            description=str(recipe.description) if recipe.description is not None else None,
            ingredients=[RecipeIngredient.model_validate(ing) for ing in recipe.ingredients]
            if recipe.ingredients is not None and isinstance(recipe.ingredients, list)
            else None,
            instructions=[RecipeInstruction.model_validate(inst) for inst in recipe.instructions]
            if recipe.instructions is not None and isinstance(recipe.instructions, list)
            else None,
            categories=[RecipeCategory.model_validate(cat) for cat in recipe.categories]
            if recipe.categories is not None and isinstance(recipe.categories, list)
            else None,
            prep_time_minutes=cast(int, recipe.prep_time_minutes)
            if recipe.prep_time_minutes is not None
            else None,
            cook_time_minutes=cast(int, recipe.cook_time_minutes)
            if recipe.cook_time_minutes is not None
            else None,
            servings=str(recipe.servings) if recipe.servings is not None else None,
            chef_notes=str(recipe.chef_notes) if recipe.chef_notes is not None else None,
            substitutions=str(recipe.substitutions) if recipe.substitutions is not None else None,
            equipment_alternatives=str(recipe.equipment_alternatives)
            if recipe.equipment_alternatives is not None
            else None,
            scaling_guidance=str(recipe.scaling_guidance)
            if recipe.scaling_guidance is not None
            else None,
            storage_notes=str(recipe.storage_notes) if recipe.storage_notes is not None else None,
            serving_suggestions=str(recipe.serving_suggestions)
            if recipe.serving_suggestions is not None
            else None,
            make_ahead_tips=str(recipe.make_ahead_tips)
            if recipe.make_ahead_tips is not None
            else None,
            coordination_timeline=str(recipe.coordination_timeline)
            if recipe.coordination_timeline is not None
            else None,
            created_at=to_utc_isostring(cast(datetime, recipe.created_at)),
            updated_at=to_utc_isostring(cast(datetime, recipe.updated_at)),
        )

    async def create_recipe(self, db: AsyncSession, params: CreateRecipeParams, flush_db: bool = True) -> UserRecipe:
        logger.debug(f"Creating recipe for user {params.user_id}")
        db_recipe = await self.repository.create_recipe(db, params, flush_db)
        return self._to_user_recipe_dto(db_recipe)

    async def get_recipe(self, db: AsyncSession, recipe_id: str) -> UserRecipe | None:
        logger.debug(f"Getting recipe {recipe_id}")
        db_recipe = await self.repository.get_recipe(db, recipe_id)
        if db_recipe is None:
            return None
        return self._to_user_recipe_dto(db_recipe)

    async def get_user_recipes(self, db: AsyncSession, user_id: str) -> list[UserRecipe]:
        logger.debug(f"Getting recipes for user {user_id}")
        db_recipes = await self.repository.get_user_recipes(db, user_id)
        return [self._to_user_recipe_dto(db_recipe) for db_recipe in db_recipes]

    async def update_recipe(self, db: AsyncSession, params: UpdateRecipeParams, flush_db: bool = True) -> UserRecipe:
        logger.debug(f"Updating recipe {params.id} with {params}")
        db_recipe = await self.repository.update_recipe(db, params, flush_db)
        return self._to_user_recipe_dto(db_recipe)

    async def update_recipe_field(
        self, db: AsyncSession, params: UpdateRecipeFieldParams, flush_db: bool = True
    ) -> UserRecipe:
        logger.debug(
            f"Updating recipe {params.id} field {params.field.name} with {params.field.value}"
        )
        db_recipe = await self.repository.update_recipe_field(db, params, flush_db)
        return self._to_user_recipe_dto(db_recipe)

    async def get_thread_recipes(self, db: AsyncSession, thread_id: str) -> list[UserRecipe]:
        logger.debug(f"Getting recipes for thread {thread_id}")
        db_recipes = await self.repository.get_thread_recipes(db, thread_id)
        return [self._to_user_recipe_dto(db_recipe) for db_recipe in db_recipes]

    async def get_recipes_by_message_id(
        self, db: AsyncSession, message_ids: list[str]
    ) -> list[UserRecipe]:
        logger.debug(f"Getting recipes for message ids {message_ids}")
        db_recipes = await self.repository.get_recipes_by_message_id(db, message_ids)
        return [self._to_user_recipe_dto(db_recipe) for db_recipe in db_recipes]

    async def create_recipes(
        self, db: AsyncSession, params: list[CreateRecipeParams], flush_db: bool = True
    ) -> list[UserRecipe]:
        logger.debug(f"Creating recipes with {params}")
        db_recipes = await self.repository.create_recipes(db, params, flush_db)
        return [self._to_user_recipe_dto(db_recipe) for db_recipe in db_recipes]

    async def update_recipe_field_by_message_id(
        self, db: AsyncSession, message_id: str, field: RecipeField, timestamp: datetime, flush_db: bool = True
    ) -> UserRecipe:
        logger.debug(f"Updating recipe field by message id {message_id} with {field}")
        db_recipe = await self.repository.update_recipe_field_by_message_id(db, message_id, field, timestamp, flush_db)
        return self._to_user_recipe_dto(db_recipe)
    
    async def update_recipe_by_message_id(self, db: AsyncSession, message_id: str, recipe: Recipe, timestamp: datetime, flush_db: bool = True) -> UserRecipe:
        logger.debug(f"Updating recipe by message id {message_id} with {recipe}")
        db_recipe = await self.repository.update_recipe_by_message_id(db, message_id, recipe, timestamp, flush_db)
        return self._to_user_recipe_dto(db_recipe)
