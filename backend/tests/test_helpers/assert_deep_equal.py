import types
from collections.abc import Mapping, Sequence
from typing import Any


def _assert_deep_equal(actual: Any, expected: Any, path: str = "") -> None:
    """
    Comprehensive deep equality assertion that compares values recursively.
    
    This function performs deep equality comparison between two objects, handling
    various data types including primitive types, sequences, mappings, Pydantic models,
    and custom objects. It provides detailed error messages with path information
    when differences are found.
    
    Args:
        actual: The actual value to compare
        expected: The expected value to compare against
        path: Current path in the object structure for error reporting (used internally)
    
    Raises:
        AssertionError: When the objects are not deeply equal, with detailed error message
            including the path where the difference was found.
    
    Examples:
        # Basic usage
        _assert_deep_equal([1, 2, 3], [1, 2, 3])  # Passes
        
        # With nested structures
        actual = {"user": {"name": "John", "age": 30}}
        expected = {"user": {"name": "John", "age": 30}}
        _assert_deep_equal(actual, expected)  # Passes
        
        # With Pydantic models
        from pydantic import BaseModel
        class User(BaseModel):
            name: str
            age: int
        
        actual = User(name="John", age=30)
        expected = User(name="John", age=30)
        _assert_deep_equal(actual, expected)  # Passes
        
        # Error example
        _assert_deep_equal([1, 2], [1, 3])
        # Raises: AssertionError: At [1]: Expected 3, but got 2
    """
    # Handle None values
    if actual is None and expected is None:
        return
    if actual is None:
        raise AssertionError(f"At {path}: Expected {expected}, but got None")
    if expected is None:
        raise AssertionError(f"At {path}: Expected None, but got {actual}")
    
    # Handle Pydantic models specifically (before type check)
    if hasattr(actual, 'model_dump') and hasattr(expected, 'model_dump'):
        # Check if they're the same type of Pydantic model
        if type(actual).__name__ != type(expected).__name__:
            raise AssertionError(f"At {path}: Type mismatch - expected {type(expected).__name__}, got {type(actual).__name__}")
        
        actual_dict = actual.model_dump()
        expected_dict = expected.model_dump()
        _assert_deep_equal(actual_dict, expected_dict, path)
        return
    
    # Handle different types (after Pydantic check)
    if type(actual) != type(expected):
        raise AssertionError(f"At {path}: Type mismatch - expected {type(expected).__name__}, got {type(actual).__name__}")
    
    # Handle primitive types (str, int, float, bool)
    if isinstance(actual, (str, int, float, bool)):
        if actual != expected:
            raise AssertionError(f"At {path}: Expected {expected!r}, but got {actual!r}")
        return
    
    # Handle sequences (list, tuple)
    if isinstance(actual, Sequence) and not isinstance(actual, (str, bytes)):
        if len(actual) != len(expected):
            raise AssertionError(f"At {path}: Length mismatch - expected {len(expected)} items, got {len(actual)} items")
        
        for i, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            _assert_deep_equal(actual_item, expected_item, f"{path}[{i}]")
        return
    
    # Handle mappings (dict)
    if isinstance(actual, Mapping):
        actual_keys = set(actual.keys())
        expected_keys = set(expected.keys())
        
        if actual_keys != expected_keys:
            missing_keys = expected_keys - actual_keys
            extra_keys = actual_keys - expected_keys
            error_msg = f"At {path}: Key mismatch"
            if missing_keys:
                error_msg += f" - missing keys: {missing_keys}"
            if extra_keys:
                error_msg += f" - extra keys: {extra_keys}"
            raise AssertionError(error_msg)
        
        for key in actual_keys:
            _assert_deep_equal(actual[key], expected[key], f"{path}.{key}")
        return
    
    # Handle custom objects with __dict__ (like regular classes)
    if hasattr(actual, '__dict__') and hasattr(expected, '__dict__'):
        actual_dict = actual.__dict__
        expected_dict = expected.__dict__
        
        # Compare __dict__ contents
        _assert_deep_equal(actual_dict, expected_dict, f"{path}.__dict__")
        return
    
    # Handle objects with custom equality
    if hasattr(actual, '__eq__') and hasattr(expected, '__eq__'):
        if actual != expected:
            raise AssertionError(f"At {path}: Objects not equal - expected {expected}, got {actual}")
        return
    
    # Handle functions and methods
    if isinstance(actual, types.FunctionType) or isinstance(actual, types.MethodType):
        if actual != expected:
            raise AssertionError(f"At {path}: Function/method mismatch")
        return
    
    # Handle other types (bytes, etc.)
    if actual != expected:
        raise AssertionError(f"At {path}: Expected {expected!r}, but got {actual!r}")


def assert_deep_equal(actual: Any, expected: Any) -> None:
    """
    Simple wrapper for deep equality assertion.
    
    This is the main function to use for deep equality comparisons in tests.
    It provides comprehensive comparison of values, not just references, and
    gives detailed error messages when differences are found.
    
    Supported data types:
    - Primitive types: str, int, float, bool, None
    - Sequences: list, tuple
    - Mappings: dict
    - Pydantic models: Any object with model_dump() method
    - Custom objects: Objects with __dict__ or __eq__ methods
    - Functions and methods
    
    Args:
        actual: The actual value to compare
        expected: The expected value to compare against
    
    Raises:
        AssertionError: When the objects are not deeply equal, with detailed error message
            showing exactly where the difference was found.
    
    Examples:
        # Basic usage in tests
        def test_user_creation():
            user = create_user("John", 30)
            assert_deep_equal(user, User(name="John", age=30))
        
        # Comparing complex nested structures
        def test_recipe_parsing():
            result = parse_recipe(xml_data)
            expected = [
                ("name", RecipeName("Pasta Carbonara")),
                ("ingredients", [
                    RecipeIngredient(name="Pasta", quantity="500", unit="g"),
                    RecipeIngredient(name="Eggs", quantity="4", unit="pieces")
                ])
            ]
            assert_deep_equal(result, expected)
        
        # Error example - shows detailed path information
        actual = {"user": {"name": "John", "age": 30}}
        expected = {"user": {"name": "Jane", "age": 30}}
        assert_deep_equal(actual, expected)
        # Raises: AssertionError: At .user.name: Expected 'Jane', but got 'John'
    
    Note:
        This function is particularly useful for testing Pydantic models and complex
        data structures where simple equality checks might not provide enough detail
        about what exactly is different between the expected and actual values.
    """
    _assert_deep_equal(actual, expected)


__all__ = ["assert_deep_equal"]
