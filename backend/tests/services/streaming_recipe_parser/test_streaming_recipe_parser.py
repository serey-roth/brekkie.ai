from typing import Tuple
import pytest

from src.schemas.recipes import (
    RecipeField,
    RecipeCategory,
    RecipeIngredient,
    RecipeInstruction,
)

from src.services.streaming_recipe_parser.streaming_recipe_parser import StreamingRecipeFieldParser

from tests.utils.assert_deep_equal import assert_deep_equal


def _get_results(parser: StreamingRecipeFieldParser, chunks: list[str]) -> list[RecipeField]:
    parser.reset()
    results = []
    for chunk in chunks:
        results.extend(parser.feed(chunk))
    return results


@pytest.fixture
def parser() -> StreamingRecipeFieldParser:
    return StreamingRecipeFieldParser()


def test_single_field_with_complete_xml(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with single field and complete xml"""
    chunks = [
        "<recipe>",
        "<name>Test Recipe</name>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="name", value="Test Recipe")])
    

def test_single_field_with_broken_open_tag(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with single field and broken open tag"""
    chunks = [
        "<recipe",
        "><na",
        "me>Test Recipe</name>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="name", value="Test Recipe")])
    
    
def test_single_field_with_split_content(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with single field and split content"""
    chunks = [
        "<recipe>",
        "<name>Test",
        " Recipe</name>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="name", value="Test Recipe")])
    
    
def test_single_field_with_broken_end_tag(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with single field and broken end tag"""
    chunks = [
        "<recipe>",
        "<name>Test Recipe</name",
        "><",
        "/recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="name", value="Test Recipe")])
    
    
def test_field_with_ampersand(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with field with ampersand"""
    chunks = [
        "<recipe>",
        "<name>Test & Recipe</name>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="name", value="Test &amp; Recipe")])
    
    chunks = [
        "<recipe>",
        "<name>Fish &amp; Chips</name>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="name", value="Fish &amp; Chips")])
    
    
def test_unknown_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with unknown field"""
    chunks = [
        "<recipe>",
        "<unknown>Test Recipe</unknown>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert results == []
    
    
def test_name_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with name field"""
    chunks = [
        "<recipe>",
        "<name>Test Recipe</name>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="name", value="Test Recipe")])
    
    chunks = [
        "<recipe>",
        "<name",
        ">Test Recipe",
        "</na",
        "me></recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="name", value="Test Recipe")])
    
    
def test_description_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with description field"""
    chunks = [
        "<recipe>",
        "<description>Test Description</description>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="description", value="Test Description")])
    
    
def test_prep_time_minutes_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with prep_time_minutes field"""
    chunks = [
        "<recipe>",
        "<prep_time_minutes>30</prep_time_minutes>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="prep_time_minutes", value=30)])
    
    
def test_cook_time_minutes_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with cook_time_minutes field"""
    chunks = [
        "<recipe>",
        "<cook_time_minutes>30</cook_time_minutes>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="cook_time_minutes", value=30)])
    
    
def test_servings_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with servings field"""
    chunks = [
        "<recipe>",
        "<servings>4</servings>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="servings", value="4")])
    
    
def test_single_ingredient(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with single ingredient"""
    chunks = [
        "<recipe>",
        "<ingredients><ingredient><ing_name>Test Ingredient</ing_name><ing_quantity>1</ing_quantity><ing_unit>cup</ing_unit></ingredient></ingredients>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="ingredient", value=RecipeIngredient(
        name="Test Ingredient",
        quantity="1",
        unit="cup" 
    )), RecipeField(name="ingredients", value=[
        RecipeIngredient(
            name="Test Ingredient",
            quantity="1",
            unit="cup"
        )
    ])])
    
    
def test_multiple_ingredients(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with multiple ingredients"""
    chunks = [
        "<recipe>",
        "<ingredients><ingredient><ing_name>Test Ingredient</ing_name><ing_quantity>1</ing_quantity><ing_unit>cup</ing_unit></ingredient><ingredient><ing_name>Test Ingredient 2</ing_name><ing_quantity>2</ing_quantity><ing_unit>cups</ing_unit></ingredient></ingredients>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="ingredient", value=RecipeIngredient(
        name="Test Ingredient",
        quantity="1",
        unit="cup"
    )), RecipeField(name="ingredient", value=RecipeIngredient(
        name="Test Ingredient 2",
        quantity="2",
        unit="cups"
    )), RecipeField(name="ingredients", value=[
        RecipeIngredient(
            name="Test Ingredient",
            quantity="1",
            unit="cup"
        ),
        RecipeIngredient(
            name="Test Ingredient 2",
            quantity="2",
            unit="cups"
        )
    ])])
    
def test_single_instruction(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with single instruction"""
    chunks = [
        "<recipe>",
        "<instructions><instruction><ins_title>Test Instruction</ins_title><ins_description>Test Step Description</ins_description></instruction></instructions>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="instruction", value=RecipeInstruction(
        title="Test Instruction",
        description="Test Step Description"
    )), RecipeField(name="instructions", value=[
        RecipeInstruction(
            title="Test Instruction",
            description="Test Step Description"
        )
    ])])
    
    
def test_multiple_instructions(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with multiple instructions"""
    chunks = [
        "<recipe>",
        "<instructions><instruction><ins_title>Test Instruction</ins_title><ins_description>Test Step Description</ins_description></instruction><instruction><ins_title>Test Instruction 2</ins_title><ins_description>Test Step Description 2</ins_description></instruction></instructions>",
        "</recipe>"
    ]
    
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="instruction", value=RecipeInstruction(
        title="Test Instruction",
        description="Test Step Description"
    )), RecipeField(name="instruction", value=RecipeInstruction(
        title="Test Instruction 2",
        description="Test Step Description 2"
    )), RecipeField(name="instructions", value=[
        RecipeInstruction(
            title="Test Instruction",
            description="Test Step Description"
        ),
        RecipeInstruction(
            title="Test Instruction 2",
            description="Test Step Description 2"
        )
    ])])
    
    
def test_single_category(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with single category"""
    chunks = [
        "<recipe>",
        "<categories><category><cat_name>Test Category</cat_name></category></categories>",
        "</recipe>"
    ]   
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="category", value=RecipeCategory(
        name="Test Category"
    )), RecipeField(name="categories", value=[
        RecipeCategory(
            name="Test Category" 
        )
    ])])
    
    
def test_multiple_categories(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with multiple categories"""
    chunks = [  
        "<recipe>",
        "<categories><category><cat_name>Test Category</cat_name></category><category><cat_name>Test Category 2</cat_name></category></categories>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks) 
    assert_deep_equal(results, [RecipeField(name="category", value=RecipeCategory(
        name="Test Category"
    )), RecipeField(name="category", value=RecipeCategory(
        name="Test Category 2"
    )), RecipeField(name="categories", value=[
        RecipeCategory(
            name="Test Category"
        ),
        RecipeCategory(
            name="Test Category 2"
        )
    ])])
    
    
def test_chef_notes_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with chef_notes field"""
    chunks = [
        "<recipe>",
        "<chef_notes>Test Chef Notes</chef_notes>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="chef_notes", value="Test Chef Notes")])
    
    
def test_substitutions_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with substitutions field"""
    chunks = [
        "<recipe>",
        "<substitutions>Test Substitutions</substitutions>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="substitutions", value="Test Substitutions")])
    
    
def test_make_ahead_tips_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with make_ahead_tips field"""
    chunks = [
        "<recipe>",
        "<make_ahead_tips>Test Make Ahead Tips</make_ahead_tips>",  
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="make_ahead_tips", value="Test Make Ahead Tips")])
    
    
def test_equipment_alternatives_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with equipment_alternatives field"""
    chunks = [
        "<recipe>",
        "<equipment_alternatives>Test Equipment Alternatives</equipment_alternatives>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="equipment_alternatives", value="Test Equipment Alternatives")])
    
    
def test_coordination_timeline_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with coordination_timeline field"""
    chunks = [
        "<recipe>",
        "<coordination_timeline>Test Coordination Timeline</coordination_timeline>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="coordination_timeline", value="Test Coordination Timeline")])
    
    
def test_scaling_guidance_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with scaling_guidance field"""
    chunks = [
        "<recipe>",
        "<scaling_guidance>Test Scaling Guidance</scaling_guidance>",
        "</recipe>"
    ]   
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="scaling_guidance", value="Test Scaling Guidance")])
    
    
def test_storage_notes_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with storage_notes field"""
    chunks = [
        "<recipe>",
        "<storage_notes>Test Storage Notes</storage_notes>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="storage_notes", value="Test Storage Notes")])
    
    
def test_serving_suggestions_field(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with serving_suggestions field"""
    chunks = [
        "<recipe>",
        "<serving_suggestions>Test Serving Suggestions</serving_suggestions>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [RecipeField(name="serving_suggestions", value="Test Serving Suggestions")])
    

def test_full_recipe_with_only_required_fields(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with full recipe with only required fields"""
    chunks = [
        "<recipe>",
        "<name>Test Recipe</name>",
        "<description>Test Description</description>",
        "<prep_time_minutes>30</prep_time_minutes>",
        "<cook_time_minutes>30</cook_time_minutes>",
        "<servings>4</servings>",
        "<categories><category><cat_name>Test Category</cat_name></category></categories>",
        "<ingredients><ingredient><ing_name>Test Ingredient</ing_name><ing_quantity>1</ing_quantity><ing_unit>cup</ing_unit></ingredient></ingredients>",
        "<instructions><instruction><ins_title>Test Instruction</ins_title><ins_description>Test Step Description</ins_description></instruction></instructions>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [
        RecipeField(name="name", value="Test Recipe"),
        RecipeField(name="description", value="Test Description"), 
        RecipeField(name="prep_time_minutes", value=30), 
        RecipeField(name="cook_time_minutes", value=30), 
        RecipeField(name="servings", value="4"),
        RecipeField(name="category", value=RecipeCategory(
            name="Test Category"
        )), 
        RecipeField(name="categories", value=[
            RecipeCategory(
                name="Test Category"
            )
        ]), 
        RecipeField(name="ingredient", value=RecipeIngredient(
            name="Test Ingredient",
            quantity="1",
            unit="cup"
        )),
        RecipeField(name="ingredients", value=[
            RecipeIngredient(
                name="Test Ingredient",
                quantity="1",
                unit="cup"
            )
        ]),
        RecipeField(name="instruction", value=RecipeInstruction(
            title="Test Instruction",
            description="Test Step Description"
        )),
        RecipeField(name="instructions", value=[
            RecipeInstruction(
                title="Test Instruction",
                description="Test Step Description"
            )
        ]),
    ])
    

def test_full_recipe_with_broken_chunks(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with full recipe with broken chunks"""
    chunks = [
        "<recipe",
        "><name>Test",
        " Recipe</name><description"
        ">Test Description</description>",
        "<prep_time"
        "_minutes>30</prep_time_minutes>",
        "<cook_time_minutes>30"
        "</cook_time_minutes>",
        "<servings>4<"
        "/servings>",
        "<categ"
        "ories><category>"
        "<cat_name>Test Category"
        "</cat_name></category></catego"
        "ries>",
        "<ingredients><ingredient><ing_name>Test Ingredient</ing_name><ing_quantity>1</ing_quantity><ing_unit>cup</ing_unit></ingredient></ingredients>",
        "<instructions><instruction><ins_title>Test Instruction</ins_title><ins_description>Test Step Description</ins_description></instruction></instructions>",
        "</recipe",
        ">"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [
        RecipeField(name="name", value="Test Recipe"),
        RecipeField(name="description", value="Test Description"), 
        RecipeField(name="prep_time_minutes", value=30), 
        RecipeField(name="cook_time_minutes", value=30), 
        RecipeField(name="servings", value="4"),
        RecipeField(name="category", value=RecipeCategory(
            name="Test Category"
        )),
        RecipeField(name="categories", value=[
            RecipeCategory(
                name="Test Category"
            )
        ]), 
        RecipeField(name="ingredient", value=RecipeIngredient(
            name="Test Ingredient",
            quantity="1",
            unit="cup"
        )),
        RecipeField(name="ingredients", value=[
            RecipeIngredient(
                name="Test Ingredient",
                quantity="1",
                unit="cup"
            )
        ]),
        RecipeField(name="instruction", value=RecipeInstruction(
            title="Test Instruction",
            description="Test Step Description"
        )),
        RecipeField(name="instructions", value=[
            RecipeInstruction(
                title="Test Instruction",
                description="Test Step Description"
            )
        ]),
    ])
    
    
def test_full_recipe_with_all_fields(parser: StreamingRecipeFieldParser):
    """Test basic recipe builder with full recipe with all fields"""
    chunks = [
        "<recipe>",
        "<name>Test Recipe</name>",
        "<description>Test Description</description>",
        "<prep_time_minutes>30</prep_time_minutes>",
        "<cook_time_minutes>30</cook_time_minutes>",
        "<servings>4</servings>",
        "<categories><category><cat_name>Test Category</cat_name></category></categories>",
        "<ingredients><ingredient><ing_name>Test Ingredient</ing_name><ing_quantity>1</ing_quantity><ing_unit>cup</ing_unit></ingredient></ingredients>",
        "<instructions><instruction><ins_title>Test Instruction</ins_title><ins_description>Test Step Description</ins_description></instruction></instructions>",
        "<chef_notes>Test Chef Notes</chef_notes>",
        "<substitutions>Test Substitutions</substitutions>",
        "<make_ahead_tips>Test Make Ahead Tips</make_ahead_tips>",
        "<equipment_alternatives>Test Equipment Alternatives</equipment_alternatives>",
        "<coordination_timeline>Test Coordination Timeline</coordination_timeline>",
        "<scaling_guidance>Test Scaling Guidance</scaling_guidance>",
        "<storage_notes>Test Storage Notes</storage_notes>",
        "<serving_suggestions>Test Serving Suggestions</serving_suggestions>",
        "</recipe>"
    ]
    
    results = _get_results(parser, chunks)
    assert_deep_equal(results, [
        RecipeField(name="name", value="Test Recipe"),
        RecipeField(name="description", value="Test Description"), 
        RecipeField(name="prep_time_minutes", value=30), 
        RecipeField(name="cook_time_minutes", value=30), 
        RecipeField(name="servings", value="4"),
        RecipeField(name="category", value=RecipeCategory(
            name="Test Category"
        )),
        RecipeField(name="categories", value=[
            RecipeCategory(
                name="Test Category"
            )
        ]), 
        RecipeField(name="ingredient", value=RecipeIngredient(
            name="Test Ingredient",
            quantity="1",
            unit="cup"
        )),
        RecipeField(name="ingredients", value=[
            RecipeIngredient(
                name="Test Ingredient",
                quantity="1",
                unit="cup"
            )
        ]),
        RecipeField(name="instruction", value=RecipeInstruction(
            title="Test Instruction",
            description="Test Step Description"
        )),
        RecipeField(name="instructions", value=[
            RecipeInstruction(
                title="Test Instruction",
                description="Test Step Description"
            )
        ]),
        RecipeField(name="chef_notes", value="Test Chef Notes"),
        RecipeField(name="substitutions", value="Test Substitutions"),
        RecipeField(name="make_ahead_tips", value="Test Make Ahead Tips"),
        RecipeField(name="equipment_alternatives", value="Test Equipment Alternatives"),
        RecipeField(name="coordination_timeline", value="Test Coordination Timeline"),
        RecipeField(name="scaling_guidance", value="Test Scaling Guidance"),
        RecipeField(name="storage_notes", value="Test Storage Notes"),
        RecipeField(name="serving_suggestions", value="Test Serving Suggestions"),
    ])
    
    