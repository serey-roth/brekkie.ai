from datetime import datetime
from typing import NewType, Literal
from pydantic import BaseModel, Field, field_validator

RecipeName = NewType("RecipeName", str)
RecipePrepTime = NewType("RecipePrepTime", str)
RecipeCookTime = NewType("RecipeCookTime", str)
RecipeServings = NewType("RecipeServings", str)
RecipeDescription = NewType("RecipeDescription", str)
RecipeMakeAheadTips = NewType("RecipeMakeAheadTips", str)
RecipeSubstitutions = NewType("RecipeSubstitutions", str)
RecipeCoordinationTimeline = NewType("RecipeCoordinationTimeline", str)
RecipeChefNotes = NewType("RecipeChefNotes", str)
RecipeEquipmentAlternatives = NewType("RecipeEquipmentAlternatives", str)
RecipeScalingGuidance = NewType("RecipeScalingGuidance", str)
RecipeStorageNotes = NewType("RecipeStorageNotes", str)
RecipeServingSuggestions = NewType("RecipeServingSuggestions", str)


class RecipeIngredient(BaseModel):
    name: str = Field(description="The name of the ingredient")
    quantity: str = Field(description="The quantity of the ingredient")
    unit: str | None = Field(default=None, description="The unit of the ingredient")


class RecipeInstruction(BaseModel):
    title: str = Field(description="The title of the instruction")
    description: str = Field(description="The description of the instruction")


class RecipeCategory(BaseModel):
    name: str = Field(description="The name of the category")


class Recipe(BaseModel):
    name: str | None = None
    description: str | None = None
    ingredients: list[RecipeIngredient] | None = None
    instructions: list[RecipeInstruction] | None = None
    categories: list[RecipeCategory] | None = None
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    servings: str | None = None

    # Optional fields
    chef_notes: str | None = None
    substitutions: str | None = None
    equipment_alternatives: str | None = None
    scaling_guidance: str | None = None
    storage_notes: str | None = None
    serving_suggestions: str | None = None
    make_ahead_tips: str | None = None
    coordination_timeline: str | None = None

    class Config:
        extra = "allow"


class UserRecipe(Recipe):
    id: str
    user_id: str
    thread_id: str
    created_at: str
    updated_at: str

    def get_recipe(self) -> Recipe:
        return Recipe(
            name=self.name,
            description=self.description,
            ingredients=self.ingredients,
            instructions=self.instructions,
            categories=self.categories,
            prep_time_minutes=self.prep_time_minutes,
            cook_time_minutes=self.cook_time_minutes,
            servings=self.servings,
            chef_notes=self.chef_notes,
            substitutions=self.substitutions,
            equipment_alternatives=self.equipment_alternatives,
            scaling_guidance=self.scaling_guidance,
            storage_notes=self.storage_notes,
            serving_suggestions=self.serving_suggestions,
            make_ahead_tips=self.make_ahead_tips,
            coordination_timeline=self.coordination_timeline,
        )


SimpleRecipeField = (
    RecipeName
    | RecipeDescription
    | RecipePrepTime
    | RecipeCookTime
    | RecipeServings
    | RecipeChefNotes
    | RecipeSubstitutions
    | RecipeEquipmentAlternatives
    | RecipeScalingGuidance
    | RecipeStorageNotes
    | RecipeServingSuggestions
    | RecipeMakeAheadTips
    | RecipeCoordinationTimeline
)
NestedRecipeField = RecipeIngredient | RecipeInstruction | RecipeCategory


class RecipeField(BaseModel):
    name: Literal[
        "name",
        "description",
        "servings",
        "chef_notes",
        "substitutions",
        "equipment_alternatives",
        "scaling_guidance",
        "storage_notes",
        "serving_suggestions",
        "make_ahead_tips",
        "coordination_timeline",
        "prep_time_minutes",
        "cook_time_minutes",
        "ingredient",
        "instruction",
        "category",
        "ingredients",
        "instructions",
        "categories",
    ]
    value: (
        str
        | int
        | RecipeIngredient
        | RecipeInstruction
        | RecipeCategory
        | list[RecipeIngredient]
        | list[RecipeInstruction]
        | list[RecipeCategory]
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v not in [
            "name",
            "description",
            "servings",
            "chef_notes",
            "substitutions",
            "equipment_alternatives",
            "scaling_guidance",
            "storage_notes",
            "serving_suggestions",
            "make_ahead_tips",
            "coordination_timeline",
            "prep_time_minutes",
            "cook_time_minutes",
            "ingredient",
            "instruction",
            "category",
            "ingredients",
            "instructions",
            "categories",
        ]:
            raise ValueError(f"Invalid recipe field name: {v}")
        return v

    @field_validator("value")
    @classmethod
    def validate_value(cls, v, info):
        """Ensure the value type matches the expected type based on the field name."""
        field_name = info.data.get("name")

        if field_name is None:
            return v

        # Integer fields
        if field_name in ["prep_time_minutes", "cook_time_minutes"]:
            if v is not None and not isinstance(v, int):
                raise ValueError(
                    f"Field '{field_name}' expects an integer value, got {type(v).__name__}"
                )

        # String fields
        elif field_name in [
            "name",
            "description",
            "servings",
            "chef_notes",
            "substitutions",
            "equipment_alternatives",
            "scaling_guidance",
            "storage_notes",
            "serving_suggestions",
            "make_ahead_tips",
            "coordination_timeline",
        ]:
            if v is not None and not isinstance(v, str):
                raise ValueError(
                    f"Field '{field_name}' expects a string value, got {type(v).__name__}"
                )

        # Single object fields
        elif field_name == "ingredient" and v is not None and not isinstance(v, RecipeIngredient):
            raise ValueError(
                f"Field '{field_name}' expects a RecipeIngredient, got {type(v).__name__}"
            )
        elif field_name == "instruction" and v is not None and not isinstance(v, RecipeInstruction):
            raise ValueError(
                f"Field '{field_name}' expects a RecipeInstruction, got {type(v).__name__}"
            )
        elif field_name == "category" and v is not None and not isinstance(v, RecipeCategory):
            raise ValueError(
                f"Field '{field_name}' expects a RecipeCategory, got {type(v).__name__}"
            )

        # List fields
        elif field_name == "ingredients" and v is not None:
            if not isinstance(v, list):
                raise ValueError(
                    f"Field '{field_name}' expects a list of RecipeIngredient, got {type(v).__name__}"
                )
            for item in v:
                if not isinstance(item, RecipeIngredient):
                    raise ValueError(
                        f"Field '{field_name}' expects list items to be RecipeIngredient, got {type(item).__name__}"
                    )
        elif field_name == "instructions" and v is not None:
            if not isinstance(v, list):
                raise ValueError(
                    f"Field '{field_name}' expects a list of RecipeInstruction, got {type(v).__name__}"
                )
            for item in v:
                if not isinstance(item, RecipeInstruction):
                    raise ValueError(
                        f"Field '{field_name}' expects list items to be RecipeInstruction, got {type(item).__name__}"
                    )
        elif field_name == "categories" and v is not None:
            if not isinstance(v, list):
                raise ValueError(
                    f"Field '{field_name}' expects a list of RecipeCategory, got {type(v).__name__}"
                )
            for item in v:
                if not isinstance(item, RecipeCategory):
                    raise ValueError(
                        f"Field '{field_name}' expects list items to be RecipeCategory, got {type(item).__name__}"
                    )

        return v


class BaseRecipeParams(BaseModel):
    """Base parameters for recipe operations."""

    name: str | None = Field(default=None, description="Recipe title/name")
    description: str | None = Field(default=None, description="Recipe overview and summary")
    ingredients: list[RecipeIngredient] | None = Field(
        default=None, description="List of ingredients with quantities"
    )
    instructions: list[RecipeInstruction] | None = Field(
        default=None, description="Step-by-step cooking instructions"
    )
    categories: list[RecipeCategory] | None = Field(
        default=None, description="Recipe tags/categories"
    )
    prep_time_minutes: int | None = Field(default=None, description="Preparation time in minutes")
    cook_time_minutes: int | None = Field(default=None, description="Cooking time in minutes")
    servings: str | None = Field(default=None, description="Number of servings")
    chef_notes: str | None = Field(default=None, description="Professional tips and techniques")
    substitutions: str | None = Field(default=None, description="Alternative ingredients")
    equipment_alternatives: str | None = Field(
        default=None, description="Alternative cooking tools"
    )
    scaling_guidance: str | None = Field(
        default=None, description="Instructions for adjusting quantities"
    )
    storage_notes: str | None = Field(default=None, description="Leftover storage guidelines")
    serving_suggestions: str | None = Field(
        default=None, description="Accompaniments and presentation ideas"
    )
    make_ahead_tips: str | None = Field(default=None, description="Advance preparation advice")
    coordination_timeline: str | None = Field(
        default=None, description="Multi-component coordination schedule"
    )


class CreateRecipeParams(BaseRecipeParams):
    """Parameters for creating a new recipe."""

    id: str = Field(description="Unique recipe identifier")
    user_id: str = Field(description="User who created the recipe")
    thread_id: str = Field(description="Conversation thread where recipe was created")
    created_at: datetime = Field(description="When the recipe was created")
    updated_at: datetime = Field(description="When the recipe was last modified")


class UpdateRecipeParams(BaseRecipeParams):
    """Parameters for updating an existing recipe."""

    id: str = Field(description="Recipe ID to update")
    updated_at: datetime = Field(description="When the recipe was last modified")


class UpdateRecipeFieldParams(BaseModel):
    """Parameters for updating a single recipe field with type safety.

    Supports string fields (name, description, etc.), integer fields (prep_time_minutes, cook_time_minutes),
    and JSON fields (ingredients, instructions, categories).
    """

    id: str = Field(description="Recipe ID to update")
    updated_at: datetime = Field(description="When the recipe was last modified")
    field: RecipeField = Field(description="Recipe field to update")
