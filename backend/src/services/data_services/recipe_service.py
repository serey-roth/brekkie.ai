from sqlalchemy.ext.asyncio import AsyncSession

from repositories.recipe_repository import RecipeRepository

from schemas.recipes import (
    CreateRecipeParams,
    UserRecipe,
    UpdateRecipeParams,
    UpdateRecipeFieldParams,
)

from utils.logger import Logger

logger = Logger("recipe_service")


class RecipeService:
    def __init__(self, repository: RecipeRepository):
        self.repository = repository
        
        
    async def create_recipe(self, db: AsyncSession, params: CreateRecipeParams) -> UserRecipe:
        logger.debug(f"Creating recipe for user {params.user_id}")
        db_recipe = await self.repository.create_recipe(db, params)
        return UserRecipe.from_db_recipe(db_recipe)
    
    
    async def get_recipe(self, db: AsyncSession, recipe_id: str) -> UserRecipe | None:
        logger.debug(f"Getting recipe {recipe_id}")
        db_recipe = await self.repository.get_recipe(db, recipe_id)
        if db_recipe is None:
            return None
        return UserRecipe.from_db_recipe(db_recipe)
    
    
    async def get_user_recipes(self, db: AsyncSession, user_id: str) -> list[UserRecipe]:
        logger.debug(f"Getting recipes for user {user_id}")
        db_recipes = await self.repository.get_user_recipes(db, user_id)
        return [UserRecipe.from_db_recipe(db_recipe) for db_recipe in db_recipes]
    
    
    async def update_recipe(self, db: AsyncSession, params: UpdateRecipeParams) -> UserRecipe:
        logger.debug(f"Updating recipe {params.id} with {params}")
        db_recipe = await self.repository.update_recipe(db, params)
        return UserRecipe.from_db_recipe(db_recipe)
    
    
    async def update_recipe_field(self, db: AsyncSession, params: UpdateRecipeFieldParams) -> UserRecipe:
        logger.debug(f"Updating recipe {params.id} field {params.field.name} with {params.field.value}")
        db_recipe = await self.repository.update_recipe_field(db, params)
        return UserRecipe.from_db_recipe(db_recipe)
    
    
    async def get_thread_recipes(self, db: AsyncSession, thread_id: str) -> list[UserRecipe]:
        logger.debug(f"Getting recipes for thread {thread_id}")
        db_recipes = await self.repository.get_thread_recipes(db, thread_id)
        return [UserRecipe.from_db_recipe(db_recipe) for db_recipe in db_recipes]
    
    
    async def get_recipes_by_message_id(self, db: AsyncSession, message_ids: list[str]) -> list[UserRecipe]:
        logger.debug(f"Getting recipes for message ids {message_ids}")
        db_recipes = await self.repository.get_recipes_by_message_id(db, message_ids)
        return [UserRecipe.from_db_recipe(db_recipe) for db_recipe in db_recipes]   
    
    
    async def create_recipes(self, db: AsyncSession, params: list[CreateRecipeParams]) -> list[UserRecipe]:
        logger.debug(f"Creating recipes with {params}")
        db_recipes = await self.repository.create_recipes(db, params)
        return [UserRecipe.from_db_recipe(db_recipe) for db_recipe in db_recipes]