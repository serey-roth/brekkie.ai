from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.schema import DBMessage, DBRecipe

from schemas.recipes import (
    CreateRecipeParams,
    RecipeIngredient,
    RecipeInstruction,
    RecipeCategory,
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
            **params.model_dump(
                exclude={"created_at", "updated_at"}, exclude_none=True, exclude_unset=True
            ),
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
        result = await db.execute(select(DBRecipe).where(DBRecipe.user_id == user_id))
        return list(result.scalars().all())

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

        items_to_update = params.model_dump(exclude={"id"}, exclude_none=True, exclude_unset=True)

        items_to_update = params.model_dump(
            exclude={"id", "updated_at"}, exclude_none=True, exclude_unset=True
        )
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
            elif field == "updated_at":
                setattr(db_recipe, field, strip_timezone(value))
            else:
                # For simple scalar fields (strings, integers), setattr works fine
                setattr(db_recipe, field, value)

        db.add(db_recipe)
        await db.flush()
        return db_recipe

    async def update_recipe_field(
        self, db: AsyncSession, params: UpdateRecipeFieldParams
    ) -> DBRecipe:
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
            if field_name == "ingredient" and isinstance(field_value, RecipeIngredient):
                current_ingredients = (
                    db_recipe.ingredients if db_recipe.ingredients is not None else []
                )
                current_ingredients = current_ingredients + [field_value.model_dump()]
                setattr(db_recipe, "ingredients", current_ingredients)

            elif field_name == "instruction" and isinstance(field_value, RecipeInstruction):
                current_instructions = (
                    db_recipe.instructions if db_recipe.instructions is not None else []
                )
                current_instructions = current_instructions + [field_value.model_dump()]
                setattr(db_recipe, "instructions", current_instructions)

            elif field_name == "category" and isinstance(field_value, RecipeCategory):
                current_categories = (
                    db_recipe.categories if db_recipe.categories is not None else []
                )
                current_categories = current_categories + [field_value.model_dump()]
                setattr(db_recipe, "categories", current_categories)

        elif field_name in ["ingredients", "instructions", "categories"]:
            if (
                field_name == "ingredients"
                and isinstance(field_value, list)
                and all(isinstance(v, RecipeIngredient) for v in field_value)
            ):
                setattr(db_recipe, "ingredients", [v.model_dump() for v in field_value])

            elif (
                field_name == "instructions"
                and isinstance(field_value, list)
                and all(isinstance(v, RecipeInstruction) for v in field_value)
            ):
                setattr(db_recipe, "instructions", [v.model_dump() for v in field_value])

            elif (
                field_name == "categories"
                and isinstance(field_value, list)
                and all(isinstance(v, RecipeCategory) for v in field_value)
            ):
                setattr(db_recipe, "categories", [v.model_dump() for v in field_value])

        else:
            setattr(db_recipe, field_name, field_value)

        setattr(db_recipe, "updated_at", strip_timezone(params.updated_at))

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
        result = await db.execute(select(DBRecipe).where(DBRecipe.thread_id == thread_id))
        return list(result.scalars().all())

    async def get_recipes_by_message_id(
        self, db: AsyncSession, message_ids: list[str]
    ) -> list[DBRecipe]:
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
        return list(result.scalars().all())

    async def create_recipes(
        self, db: AsyncSession, params: list[CreateRecipeParams]
    ) -> list[DBRecipe]:
        """Creates recipes in the database.

        Args:
            db: Database session for the operation
            params: List of recipe creation parameters
        """
        db_recipes = [
            DBRecipe(
                created_at=strip_timezone(recipe.created_at),
                updated_at=strip_timezone(recipe.updated_at),
                **recipe.model_dump(
                    exclude={"created_at", "updated_at"}, exclude_none=True, exclude_unset=True
                ),
            )
            for recipe in params
        ]
        db.add_all(db_recipes)
        await db.flush()
        return db_recipes
