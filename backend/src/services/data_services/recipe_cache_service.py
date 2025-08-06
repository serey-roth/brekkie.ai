from typing import Any, Optional, Type

from pydantic import BaseModel
from schemas.recipes import (
    CreateRecipeParams,
    RecipeCategory,
    RecipeIngredient,
    RecipeInstruction,
    UpdateRecipeFieldParams,
    UpdateRecipeParams,
    UserRecipe,
)
from services.redis.redis_cache import RedisCache
from services.redis.redis_client import RedisClient
from utils.date_utils import to_utc_isostring


class RecipeCacheService:
    def __init__(self, redis_client: RedisClient, ttl: int):
        self.recipe_cache = RedisCache[UserRecipe](redis_client)
        self.ttl = ttl

    def _get_recipe_key(self, user_id: str, thread_id: str, recipe_id: str) -> str:
        return f"brekkie:chat_session:{user_id}:threads:{thread_id}:recipes:{recipe_id}"

    def _get_all_recipes_key(self, user_id: str, thread_id: str) -> str:
        return f"brekkie:chat_session:{user_id}:threads:{thread_id}:recipes:*"

    def _get_all_user_recipes_key(self, user_id: str) -> str:
        return f"brekkie:chat_session:{user_id}:threads:*:recipes:*"

    def _get_all_thread_recipes_key(self, thread_id: str) -> str:
        return f"brekkie:chat_session:*:threads:{thread_id}:recipes:*"

    async def get_recipe(self, user_id: str, thread_id: str, recipe_id: str) -> UserRecipe | None:
        return await self.recipe_cache.get_json(
            self._get_recipe_key(user_id, thread_id, recipe_id), UserRecipe
        )

    async def get_recipes(self, user_id: str, thread_id: str) -> list[UserRecipe]:
        result = await self.recipe_cache.get_all_json_by_pattern(
            pattern=self._get_all_recipes_key(user_id, thread_id), model=UserRecipe
        )
        return list(result)

    async def get_user_recipes(self, user_id: str) -> list[UserRecipe]:
        result = await self.recipe_cache.get_all_json_by_pattern(
            pattern=self._get_all_user_recipes_key(user_id), model=UserRecipe
        )
        return list(result)

    async def get_thread_recipes(self, thread_id: str) -> list[UserRecipe]:
        result = await self.recipe_cache.get_all_json_by_pattern(
            pattern=self._get_all_thread_recipes_key(thread_id), model=UserRecipe
        )
        return list(result)

    async def get_recipes_by_ids(
        self, user_id: str, thread_id: str, recipe_ids: list[str]
    ) -> list[UserRecipe]:
        keys = [self._get_recipe_key(user_id, thread_id, recipe_id) for recipe_id in recipe_ids]
        result = await self.recipe_cache.get_all_json_by_keys(keys=keys, model=UserRecipe)
        return list(result)

    async def set_recipe(
        self, recipe: UserRecipe, ttl: int | None = None, keep_ttl: bool = False
    ) -> None:
        if keep_ttl:
            set_ttl = None
        else:
            set_ttl = ttl if ttl is not None else self.ttl
        await self.recipe_cache.set_json(
            self._get_recipe_key(recipe.user_id, recipe.thread_id, recipe.id),
            recipe,
            ttl=set_ttl,
            keep_ttl=keep_ttl,
        )

    async def create_recipe(self, params: CreateRecipeParams, ttl: int | None = None) -> UserRecipe:
        recipe = UserRecipe(
            created_at=to_utc_isostring(params.created_at),
            updated_at=to_utc_isostring(params.updated_at),
            **params.model_dump(
                exclude={"created_at", "updated_at"}, exclude_unset=True, exclude_none=True
            ),
        )
        await self.set_recipe(recipe, ttl=ttl)
        return recipe

    async def update_recipe_field(
        self, user_id: str, thread_id: str, params: UpdateRecipeFieldParams
    ) -> UserRecipe:
        recipe = await self.get_recipe(user_id, thread_id, params.id)
        if recipe is None:
            raise ValueError(f"Recipe {params.id} not found")

        new_recipe = recipe.model_copy(deep=True)
        field_name = params.field.name
        field_value = params.field.value

        if field_name in ["ingredient", "instruction", "category"]:
            if field_name == "ingredient" and isinstance(field_value, RecipeIngredient):
                if new_recipe.ingredients is None:
                    new_recipe.ingredients = []
                new_recipe.ingredients = new_recipe.ingredients + [field_value]
            elif field_name == "instruction" and isinstance(field_value, RecipeInstruction):
                if new_recipe.instructions is None:
                    new_recipe.instructions = []
                new_recipe.instructions = new_recipe.instructions + [field_value]
            elif field_name == "category" and isinstance(field_value, RecipeCategory):
                if new_recipe.categories is None:
                    new_recipe.categories = []
                new_recipe.categories = new_recipe.categories + [field_value]
            else:
                raise ValueError(f"Invalid field value: {field_value} for field {field_name}")

        elif field_name in ["ingredients", "instructions", "categories"]:
            if (
                field_name == "ingredients"
                and isinstance(field_value, list)
                and all(isinstance(item, RecipeIngredient) for item in field_value)
            ):
                new_recipe = new_recipe.model_copy(update={"ingredients": field_value})
            elif (
                field_name == "instructions"
                and isinstance(field_value, list)
                and all(isinstance(item, RecipeInstruction) for item in field_value)
            ):
                new_recipe = new_recipe.model_copy(update={"instructions": field_value})
            elif (
                field_name == "categories"
                and isinstance(field_value, list)
                and all(isinstance(item, RecipeCategory) for item in field_value)
            ):
                new_recipe = new_recipe.model_copy(update={"categories": field_value})
            else:
                raise ValueError(f"Invalid field value: {field_value} for field {field_name}")

        else:
            setattr(new_recipe, field_name, field_value)

        new_recipe.updated_at = to_utc_isostring(params.updated_at)

        previous_ttl = await self.recipe_cache.get_ttl(
            self._get_recipe_key(user_id, thread_id, params.id)
        )
        if previous_ttl is None or previous_ttl < 0:
            await self.set_recipe(new_recipe, ttl=self.ttl)
        else:
            await self.set_recipe(new_recipe, keep_ttl=True)

        return new_recipe

    def _ensure_models(
        self, data: Optional[list[Any]], model_cls: Type[BaseModel]
    ) -> list[BaseModel]:
        if not data:
            return []
        return [item if isinstance(item, model_cls) else model_cls(**item) for item in data]

    async def update_recipe(
        self, user_id: str, thread_id: str, params: UpdateRecipeParams
    ) -> UserRecipe:
        recipe = await self.get_recipe(user_id, thread_id, params.id)
        if recipe is None:
            raise ValueError(f"Recipe {params.id} not found in session {user_id}:{thread_id}")

        new_recipe = recipe.model_copy(deep=True)

        if params.ingredients is not None:
            new_recipe = new_recipe.model_copy(
                update={"ingredients": self._ensure_models(params.ingredients, RecipeIngredient)}
            )
        if params.instructions is not None:
            new_recipe = new_recipe.model_copy(
                update={"instructions": self._ensure_models(params.instructions, RecipeInstruction)}
            )
        if params.categories is not None:
            new_recipe = new_recipe.model_copy(
                update={"categories": self._ensure_models(params.categories, RecipeCategory)}
            )

        for key, value in params.model_dump(
            exclude={"id", "updated_at", "ingredients", "instructions", "categories"},
            exclude_unset=True,
            exclude_none=True,
        ).items():
            setattr(new_recipe, key, value)

        new_recipe.updated_at = to_utc_isostring(params.updated_at)

        previous_ttl = await self.recipe_cache.get_ttl(
            self._get_recipe_key(user_id, thread_id, params.id)
        )
        if previous_ttl is None or previous_ttl < 0:
            await self.set_recipe(new_recipe, ttl=self.ttl)
        else:
            await self.set_recipe(new_recipe, keep_ttl=True)

        return new_recipe
