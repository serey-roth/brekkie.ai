import re
from typing import Callable, List, Literal

from lxml.etree import XMLPullParser, XMLSyntaxError
from schemas.recipes import (
    Recipe,
    RecipeCategory,
    RecipeField,
    RecipeIngredient,
    RecipeInstruction,
)
from services.streaming_recipe_parser.xml_chunk_tokenizer import XMLChunkTokenizer
from services.streaming_recipe_parser.xml_chunk_patcher import XMLChunkPatcher
from services.streaming_recipe_parser.xml_tag_tracker import XMLTagTracker
from utils.logger import Logger

logger = Logger("streaming_recipe_parser", level="WARNING")


class StreamingRecipeFieldParser:
    """
    Parses streaming XML recipe data into structured field data.

    This parser is designed to handle streaming XML content that represents
    recipe data. It processes XML chunks incrementally and extracts recipe
    fields as they become available. The parser supports both required and
    optional recipe fields, including nested structures like ingredients,
    instructions, and categories.

    The parser uses a multi-stage approach:
    1. XML chunk patching to handle incomplete tags across chunk boundaries
    2. XML tokenization to break content into structured tokens
    3. Tag tracking to manage nested XML structures
    4. Field-specific handlers to extract and structure recipe data

    Supported recipe fields:
    - Required: name, description, prep_time_minutes, cook_time_minutes,
               servings, ingredients, instructions, categories
    - Optional: chef_notes, substitutions, make_ahead_tips,
                equipment_alternatives, coordination_timeline, scaling_guidance,
                storage_notes, serving_suggestions

    Nested structures:
    - Ingredients: ing_name, ing_quantity, ing_unit
    - Instructions: ins_title, ins_description
    - Categories: cat_name

    Attributes:
        known_tags (set): Set of all supported XML tag names
        tokenizer (XMLChunkTokenizer): Tokenizer for XML content
        tracker (MultiTagXMLTracker): Tracker for nested XML structures
        patcher (XMLChunkPatcher): Patcher for incomplete XML chunks
        parsed_fields (set): Set of fields that have been successfully parsed
        current_ingredient (dict): Current ingredient being built
        current_instruction (dict): Current instruction being built
        current_category (dict): Current category being built
        recipe (Recipe): The recipe object being constructed

    Examples:
        >>> parser = StreamingRecipeFieldParser()
        >>> results = parser.feed("<recipe><name>Test Recipe</name></recipe>")
        >>> results
        [RecipeField(name="name", value="Test Recipe")]

        >>> parser.feed("<ingredients><ingredient><ing_name>Flour</ing_name><ing_quantity>2</ing_quantity><ing_unit>cups</ing_unit></ingredient></ingredients>")
        >>> results
        [RecipeField(name="ingredient", value=RecipeIngredient(name="Flour", quantity="2", unit="cups")),
         RecipeField(name="ingredients", value=[RecipeIngredient(...)])]
    """

    def __init__(
        self,
    ):
        """
        Initialize the streaming recipe field parser.

        Sets up all necessary components for parsing streaming XML recipe data,
        including the tokenizer, tracker, patcher, and field handlers.
        """
        self.known_tags = {
            "name",
            "description",
            "prep_time_minutes",
            "cook_time_minutes",
            "servings",
            "ingredients",
            "ingredient",
            "ing_name",
            "ing_quantity",
            "ing_unit",
            "instructions",
            "instruction",
            "ins_title",
            "ins_description",
            "categories",
            "category",
            "cat_name",
            "chef_notes",
            "substitutions",
            "make_ahead_tips",
            "equipment_alternatives",
            "coordination_timeline",
            "scaling_guidance",
            "storage_notes",
            "serving_suggestions",
        }

        self.tokenizer = XMLChunkTokenizer()
        self.tracker = XMLTagTracker(known_tags=self.known_tags)
        self.patcher = XMLChunkPatcher()

        self.parsed_fields = set()

        self.current_ingredient = None
        self.current_instruction = None
        self.current_category = None

        self.recipe = Recipe()

    @property
    def tag_handlers(self) -> dict[str, Callable[[str, str], RecipeField | None]]:
        """
        Get the mapping of tag names to their handler functions.

        Returns:
            dict[str, Callable[[str, str], RecipeField | None]]: Mapping of tag names to handler functions that process the XML elements and return RecipeField objects.
        """
        return {
            # Required fields
            "name": self._handle_simple_field,
            "description": self._handle_simple_field,
            "prep_time_minutes": self._handle_simple_field,
            "cook_time_minutes": self._handle_simple_field,
            "servings": self._handle_simple_field,
            ## Child fields
            "ing_name": lambda tag, text: self._handle_child_field(
                parent_tag="ingredient", child_tag=tag, text=text
            ),
            "ing_quantity": lambda tag, text: self._handle_child_field(
                parent_tag="ingredient", child_tag=tag, text=text
            ),
            "ing_unit": lambda tag, text: self._handle_child_field(
                parent_tag="ingredient", child_tag=tag, text=text
            ),
            "ins_title": lambda tag, text: self._handle_child_field(
                parent_tag="instruction", child_tag=tag, text=text
            ),
            "ins_description": lambda tag, text: self._handle_child_field(
                parent_tag="instruction", child_tag=tag, text=text
            ),
            "cat_name": lambda tag, text: self._handle_child_field(
                parent_tag="category", child_tag=tag, text=text
            ),
            ## Nested fields
            "ingredient": lambda tag, text: self._handle_nested_field(name="ingredient"),
            "instruction": lambda tag, text: self._handle_nested_field(name="instruction"),
            "category": lambda tag, text: self._handle_nested_field(name="category"),
            ## Container fields
            "ingredients": lambda tag, text: self._handle_container_field(name="ingredients"),
            "instructions": lambda tag, text: self._handle_container_field(name="instructions"),
            "categories": lambda tag, text: self._handle_container_field(name="categories"),
            # Optional fields
            "chef_notes": self._handle_simple_field,
            "substitutions": self._handle_simple_field,
            "make_ahead_tips": self._handle_simple_field,
            "equipment_alternatives": self._handle_simple_field,
            "coordination_timeline": self._handle_simple_field,
            "scaling_guidance": self._handle_simple_field,
            "storage_notes": self._handle_simple_field,
            "serving_suggestions": self._handle_simple_field,
        }

    def feed(self, chunk: str) -> List[RecipeField]:
        """
        Feed a chunk of XML content to the parser.

        This method processes incoming XML chunks by:
        1. Patching incomplete XML tags across chunk boundaries
        2. Tokenizing the patched content
        3. Tracking nested XML structures
        4. Extracting completed recipe fields

        Args:
            chunk (str): XML chunk to process

        Returns:
            List[RecipeField]: List of RecipeField objects for fields that were completed in this chunk.

        Examples:
            >>> parser = StreamingRecipeFieldParser()
            >>> parser.feed("<recipe><name>Test Recipe</name></recipe>")
            [RecipeField(name="name", value="Test Recipe")]
        """
        patched_chunk = self.patcher.patch(chunk)

        if not patched_chunk:
            return []

        logger.debug(f"Patched chunk: {patched_chunk}")
        return self._process_chunk(patched_chunk)

    def _process_chunk(self, chunk: str) -> List[RecipeField]:
        """
        Process a chunk of XML content and return parsed fields.

        This internal method handles the core parsing logic:
        1. Escapes ampersands in the XML content
        2. Tokenizes the XML into structured tokens
        3. Tracks nested XML structures
        4. Parses completed tags into recipe fields

        Args:
            chunk (str): Complete XML chunk to process

        Returns:
            List[RecipeField]: List of RecipeField objects for fields that were completed in this chunk.
        """
        chunk = self._escape_ampersands(chunk)
        tokens = self.tokenizer.tokenize(chunk)

        results: list[RecipeField] = []
        for typ, tag, text, raw in tokens:
            complete = self.tracker.track(typ, tag, text, raw)
            if complete is None:
                continue

            for tag_name, xml_buffer in complete:
                logger.debug(f"Processing tag: {tag_name}: {xml_buffer}")
                parsed = self._safe_parse(tag_name, xml_buffer)
                if parsed:
                    results.append(parsed)

        return results

    def _safe_parse(self, tag: str, xml_fragment: str) -> RecipeField | None:
        """
        Safely parse an XML fragment using a pull parser.

        This method uses lxml's XMLPullParser to parse XML fragments safely,
        handling malformed XML gracefully by catching XMLSyntaxError exceptions.

        Args:
            tag (str): The tag name to look for in the XML fragment
            xml_fragment (str): The XML fragment to parse

        Returns:
            RecipeField | None: RecipeField object if parsing succeeds, or None if parsing fails or the tag is not found
        """
        try:
            parser = XMLPullParser(events=("end",))
            parser.feed(xml_fragment)
            for _, elem in parser.read_events():
                elem_tag = elem.tag.lower() if hasattr(elem, "tag") else None
                # Only process the specific tag we're looking for
                if (
                    elem_tag is None
                    or not isinstance(elem_tag, str)
                    or elem_tag != tag
                    or elem_tag not in self.known_tags
                ):
                    continue

                text = "".join(elem.itertext()).strip()
                text = self._escape_ampersands(text)
                if len(text) == 0:
                    continue

                handler = self.tag_handlers.get(elem_tag)
                if handler:
                    return handler(elem_tag, text)

        except XMLSyntaxError:
            pass

        return None

    def _escape_ampersands(self, text: str) -> str:
        """
        Escape unescaped ampersands in XML content.

        This method ensures that ampersands in XML content are properly escaped
        as &amp; to maintain valid XML syntax.

        Args:
            text (str): Text content that may contain unescaped ampersands

        Returns:
            str: Text with ampersands properly escaped
        """
        return re.sub(r"&(?!(amp|lt|gt|quot|apos);)", "&amp;", text)

    def _handle_simple_field(self, tag: str, text: str) -> RecipeField | None:
        """
        Handle a simple recipe field.

        Simple fields contain simple text content without nested structures.
        Examples include name, description, prep_time_minutes, etc.

        Args:
            tag (str): The tag name of the field
            text (str): The text content of the field

        Returns:
            RecipeField | None: Simple field (e.g. name/description/prep_time_minutes/cook_time_minutes/servings/etc), or None if the field is invalid or already parsed
        """
        logger.debug(f"Standalone field: {tag}: {text}")

        self.parsed_fields.add(tag)

        match tag:
            case "name":
                self.recipe.name = text
                return RecipeField(name="name", value=text)
            case "description":
                self.recipe.description = text
                return RecipeField(name="description", value=text)
            case "prep_time_minutes":
                value = int(text)
                self.recipe.prep_time_minutes = value
                return RecipeField(name="prep_time_minutes", value=value)
            case "cook_time_minutes":
                value = int(text)
                self.recipe.cook_time_minutes = value
                return RecipeField(name="cook_time_minutes", value=value)
            case "servings":
                self.recipe.servings = text
                return RecipeField(name="servings", value=text)
            case "chef_notes":
                self.recipe.chef_notes = text
                return RecipeField(name="chef_notes", value=text)
            case "substitutions":
                self.recipe.substitutions = text
                return RecipeField(name="substitutions", value=text)
            case "equipment_alternatives":
                self.recipe.equipment_alternatives = text
                return RecipeField(name="equipment_alternatives", value=text)
            case "scaling_guidance":
                self.recipe.scaling_guidance = text
                return RecipeField(name="scaling_guidance", value=text)
            case "storage_notes":
                self.recipe.storage_notes = text
                return RecipeField(name="storage_notes", value=text)
            case "serving_suggestions":
                self.recipe.serving_suggestions = text
                return RecipeField(name="serving_suggestions", value=text)
            case "make_ahead_tips":
                self.recipe.make_ahead_tips = text
                return RecipeField(name="make_ahead_tips", value=text)
            case "coordination_timeline":
                self.recipe.coordination_timeline = text
                return RecipeField(name="coordination_timeline", value=text)
            case _:
                return None

    def _handle_child_field(
        self,
        parent_tag: Literal["ingredient", "instruction", "category"],
        child_tag: str,
        text: str,
    ) -> None:
        """
        Handle a child field within a nested structure.

        Child fields are components of larger nested structures like ingredients,
        instructions, or categories. This method extracts the child field value
        and stores it in the appropriate current object.

        Args:
            parent_tag (str): Name of the parent tag (e.g., "ingredient", "instruction", "category")
            child_tag (str): Name of the child tag (e.g., "ing_name", "ing_quantity", "ins_title")
            text (str): The text content of the child field

        Returns:
            None: Child fields don't produce immediate results, they are stored
                in the current object for later processing when the parent is completed
        """
        logger.debug(f"Child field: {parent_tag} -> {child_tag}: {text}")

        match parent_tag:
            case "ingredient":
                if self.current_ingredient is None:
                    self.current_ingredient = {}
                # Remove the ing_ prefix from the child tag
                self.current_ingredient[child_tag.replace("ing_", "")] = text

            case "instruction":
                if self.current_instruction is None:
                    self.current_instruction = {}
                self.current_instruction[child_tag.replace("ins_", "")] = text

            case "category":
                if self.current_category is None:
                    self.current_category = {}
                # Remove the cat_ prefix from the child tag
                self.current_category[child_tag.replace("cat_", "")] = text

            case _:
                pass

        return None

    def _handle_nested_field(
        self, name: Literal["ingredient", "instruction", "category"]
    ) -> RecipeField | None:
        """
        Handle a nested field that contains child fields.

        Nested fields represent complete structures like individual ingredients,
        instructions, or categories. When a nested field is completed, it
        contains all its child fields and is added to the appropriate collection.

        Args:
            name (str): Name of the nested field ("ingredient", "instruction", "category")

        Returns:
            RecipeField | None: Nested field (e.g. ingredient/instruction/category), or None if the field is invalid or empty
        """
        logger.debug(f"Nested field: {name}")

        match name:
            case "ingredient":
                if self.current_ingredient is None:
                    return None

                if self.recipe.ingredients is None:
                    self.recipe.ingredients = []
                self.recipe.ingredients.append(
                    RecipeIngredient(
                        name=self.current_ingredient.get("name", ""),
                        quantity=self.current_ingredient.get("quantity", ""),
                        unit=self.current_ingredient.get("unit", ""),
                    )
                )
                self.current_ingredient = None
                return RecipeField(name="ingredient", value=self.recipe.ingredients[-1])

            case "instruction":
                if self.current_instruction is None:
                    return None

                if self.recipe.instructions is None:
                    self.recipe.instructions = []
                self.recipe.instructions.append(
                    RecipeInstruction(
                        title=self.current_instruction.get("title", ""),
                        description=self.current_instruction.get("description", ""),
                    )
                )
                self.current_instruction = None
                return RecipeField(name="instruction", value=self.recipe.instructions[-1])

            case "category":
                if self.current_category is None:
                    return None

                if self.recipe.categories is None:
                    self.recipe.categories = []
                self.recipe.categories.append(
                    RecipeCategory(
                        name=self.current_category.get("name", ""),
                    )
                )
                self.current_category = None
                return RecipeField(name="category", value=self.recipe.categories[-1])

            case _:
                return None

    def _handle_container_field(
        self, name: Literal["ingredients", "instructions", "categories"]
    ) -> RecipeField | None:
        """
        Handle a container field that holds collections of nested fields.

        Container fields represent collections of nested structures like
        ingredients, instructions, or categories. When a container field
        is completed, it contains all the nested fields that were parsed.

        Args:
            name (str): Name of the container field ("ingredients", "instructions", "categories")

        Returns:
            RecipeField | None: List of container fields (e.g. ingredients/instructions/categories), or None if the field is invalid
        """
        logger.debug(f"Container field: {name}")

        self.parsed_fields.add(name)

        match name:
            case "ingredients":
                if self.recipe.ingredients is None:
                    return None
                return RecipeField(name="ingredients", value=self.recipe.ingredients)
            case "instructions":
                if self.recipe.instructions is None:
                    return None
                return RecipeField(name="instructions", value=self.recipe.instructions)
            case "categories":
                if self.recipe.categories is None:
                    return None
                return RecipeField(name="categories", value=self.recipe.categories)
            case _:
                return None

    def get_recipe(self) -> Recipe:
        """
        Get the complete recipe object.

        Returns:
            Recipe: The recipe object containing all parsed fields
        """
        return self.recipe

    def reset(self):
        """
        Reset the parser state for processing a new recipe.

        This method clears all internal state including:
        - XML patcher buffer
        - Tag tracker stack
        - Parsed fields set
        - Current nested objects (ingredient, instruction, category)
        - Recipe object

        This should be called when starting to parse a new recipe document.
        """
        self.patcher.reset()
        self.tracker.reset()
        self.parsed_fields = set()
        self.current_ingredient = None
        self.current_instruction = None
        self.current_category = None
        self.recipe = Recipe()
