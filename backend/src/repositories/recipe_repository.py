from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.schema import DBMessage, DBRecipe

from schemas.recipes import (
    CreateRecipeParams,
    UpdateRecipeParams,
    UpdateRecipeFieldParams,
)

from utils.date_utils import strip_timezone


class RecipeRepository:
    """Repository for managing recipe database operations including creation, retrieval, updates, and field-specific modifications."""
    
    async def create_recipe(self, db: AsyncSession, params: CreateRecipeParams) -> DBRecipe:
        """Creates a new recipe record with the given parameters.
        
        Args:
            db: Database session for the operation
            params: Recipe creation parameters including user_id, thread_id, and recipe fields
            
        Returns:
            The newly created recipe record
        """
        db_recipe = DBRecipe(
            created_at=strip_timezone(params.created_at),
            updated_at=strip_timezone(params.updated_at),
            **params.model_dump(exclude={"created_at", "updated_at"}, exclude_none=True, exclude_unset=True)
        )
        db.add(db_recipe)
        await db.flush()
        return db_recipe
    
    
    async def get_recipe(self, db: AsyncSession, recipe_id: str) -> DBRecipe | None:
        """Gets a single recipe record with the given id.
        
        Args:
            db: Database session for the operation
            recipe_id: The recipe's id
            
        Returns:
            Recipe record if found, None otherwise
        """
        result = await db.get(DBRecipe, recipe_id)
        return result
    
    
    async def get_user_recipes(self, db: AsyncSession, user_id: str) -> list[DBRecipe]:
        """Gets all recipes created by a specific user.
        
        Args:
            db: Database session for the operation
            user_id: The user's id
            
        Returns:
            List of recipes created by the user
        """
        result = await db.execute(
            select(DBRecipe).where(DBRecipe.user_id == user_id)
        )
        return result.scalars().all()
    
    
    async def update_recipe(self, db: AsyncSession, params: UpdateRecipeParams) -> DBRecipe:
        """Updates an existing recipe record with the given parameters.
        
        Args:
            db: Database session for the operation
            params: Update parameters containing the recipe id and recipe fields to update
            
        Returns:
            The updated recipe record
            
        Raises:
            ValueError: If the recipe doesn't exist
        """
        db_recipe = await db.get(DBRecipe, params.id)
        if db_recipe is None:
            raise ValueError(f"Recipe {params.id} not found")
        
        items_to_update = params.model_dump(exclude={"id", "updated_at"}, exclude_none=True, exclude_unset=True)
        for field, value in items_to_update.items():
            if value is None:
                continue
            
            # Special handling for JSON fields: ingredients, instructions, and categories
            # These are stored as JSON in the database and come as lists of Pydantic models
            # that have already been serialized to dicts via model_dump()
            if field == "ingredients":
                db_recipe.ingredients = value
            elif field == "instructions":
                db_recipe.instructions = value
            elif field == "categories":
                db_recipe.categories = value
            else:
                # For simple scalar fields (strings, integers), setattr works fine
                setattr(db_recipe, field, value)
                
        db_recipe.updated_at = strip_timezone(params.updated_at)
        
        db.add(db_recipe)
        await db.flush()
        return db_recipe
    
    
    async def update_recipe_field(self, db: AsyncSession, params: UpdateRecipeFieldParams) -> DBRecipe:
        """Updates a single field of an existing recipe record.
        
        Args:
            db: Database session for the operation
            params: Field update parameters with type-safe field and value
            
        Returns:
            The updated recipe record
            
        Raises:
            ValueError: If the recipe doesn't exist or if the value type doesn't match the field
        """
        db_recipe = await db.get(DBRecipe, params.id)
        if db_recipe is None:
            raise ValueError(f"Recipe {params.id} not found")
        
        field_name = params.field.name
        field_value = params.field.value
        if field_name in ["ingredient", "instruction", "category"]:
            if field_name == "ingredient":
                if db_recipe.ingredients is None:
                    db_recipe.ingredients = []
                db_recipe.ingredients = db_recipe.ingredients + [field_value.model_dump()]
                
            elif field_name == "instruction":
                if db_recipe.instructions is None:
                    db_recipe.instructions = []
                db_recipe.instructions = db_recipe.instructions + [field_value.model_dump()]
                
            elif field_name == "category":
                if db_recipe.categories is None:
                    db_recipe.categories = []
                db_recipe.categories = db_recipe.categories + [params.field.value.model_dump()]
                
        elif field_name in ["ingredients", "instructions", "categories"]:
            if field_name == "ingredients":
                db_recipe.ingredients = [v.model_dump() for v in field_value]
            elif field_name == "instructions":
                db_recipe.instructions = [v.model_dump() for v in field_value]
            elif field_name == "categories":
                db_recipe.categories = [v.model_dump() for v in field_value]
                
        else:
            setattr(db_recipe, field_name, field_value)
            
        db_recipe.updated_at = strip_timezone(params.updated_at)
        
        db.add(db_recipe)
        await db.flush()
        return db_recipe
        
    
    async def get_thread_recipes(self, db: AsyncSession, thread_id: str) -> list[DBRecipe]:
        """Gets all recipes associated with a specific thread.
        
        Args:
            db: Database session for the operation
            thread_id: The thread's id
            
        Returns:
            List of recipes associated with the thread
        """
        result = await db.execute(
            select(DBRecipe).where(DBRecipe.thread_id == thread_id)
        )
        return result.scalars().all()
    
    
    async def get_recipes_by_message_id(self, db: AsyncSession, message_ids: list[str]) -> list[DBRecipe]:
        """Gets recipes associated with specific message ids.
        
        Args:
            db: Database session for the operation
            message_ids: List of message ids
            
        Returns:
            List of recipes associated with the specified messages
        """
        result = await db.execute(
            select(DBRecipe)
            .join(DBMessage, DBRecipe.id == DBMessage.recipe_id)
            .where(DBMessage.id.in_(message_ids))
            .where(DBMessage.recipe_id.isnot(None))
        )
        return result.scalars().all()
    
    
    async def create_recipes(self, db: AsyncSession, params: list[CreateRecipeParams]) -> list[DBRecipe]:
        """Creates recipes in the database.
        
        Args:
            db: Database session for the operation
            params: List of recipe creation parameters
        """
        db_recipes = [DBRecipe(
            created_at=strip_timezone(recipe.created_at),
            updated_at=strip_timezone(recipe.updated_at),
            **recipe.model_dump(exclude={"created_at", "updated_at"}, exclude_none=True, exclude_unset=True)
        ) for recipe in params]
        db.add_all(db_recipes)
        await db.flush()
        return db_recipes
    