import pytest

from src.services.streaming_recipe_parser.xm_chunk_tokenizer import XMLChunkTokenizer

@pytest.fixture
def tokenizer():
    return XMLChunkTokenizer()


def test_basic_xml_tokenization(tokenizer):
    """Test basic XML tokenization with well-formed tags"""
    chunk = "<recipe><name>Test Recipe</name></recipe>"
    tokens = tokenizer.tokenize(chunk)
    
    expected = [
        ("start", "recipe", None, "<recipe>"),
        ("start", "name", None, "<name>"),
        ("text", None, "Test Recipe", "Test Recipe"),
        ("end", "name", None, "</name>"),
        ("end", "recipe", None, "</recipe>")
    ]
    assert tokens == expected

def test_text_only_chunk(tokenizer):
    """Test tokenization of plain text without XML tags"""
    chunk = "This is plain text content"
    tokens = tokenizer.tokenize(chunk)
    
    expected = [("text", None, "This is plain text content", "This is plain text content")]
    assert tokens == expected


def test_malformed_xml_chunk(tokenizer):
    """Test tokenization of malformed XML - missing closing angle bracket"""
    # Missing closing bracket
    chunk = "<recipe<name>Test"
    tokens = tokenizer.tokenize(chunk)
    
    # <recipe is not a valid XML tag, but it's valid text
    expected = [
        ("text", None, "recipe", "recipe"),
        ("start", "name", None, "<name>"),
        ("text", None, "Test", "Test"),
    ]
    assert tokens == expected


def test_incomplete_xml_chunk(tokenizer):
    """Test tokenization of incomplete XML tags"""
    chunk = "<recipe><name>Test Recipe"
    tokens = tokenizer.tokenize(chunk)
    
    expected = [
        ("start", "recipe", None, "<recipe>"),
        ("start", "name", None, "<name>"),
        ("text", None, "Test Recipe", "Test Recipe")
    ]
    assert tokens == expected


def test_unescaped_text_chunk(tokenizer):
    """Test tokenization with unescaped special characters"""
    chunk = "<description>Fish & Chips with salt & pepper</description>"
    tokens = tokenizer.tokenize(chunk)
    
    expected = [
        ("start", "description", None, "<description>"),
        ("text", None, "Fish & Chips with salt & pepper", "Fish & Chips with salt & pepper"),
        ("end", "description", None, "</description>")
    ]
    assert tokens == expected


def test_newlines_and_whitespace_chunk(tokenizer):
    """Test tokenization with newlines and extra spaces"""
    chunk = """<recipe>
<name>
    Test Recipe
</name>
</recipe>"""
    tokens = tokenizer.tokenize(chunk)
    
    expected = [
        ("start", "recipe", None, "<recipe>"),
        ("text", None, "\n", "\n"),
        ("start", "name", None, "<name>"),
        ("text", None, "\n    Test Recipe\n", "\n    Test Recipe\n"),
        ("end", "name", None, "</name>"),
        ("text", None, "\n", "\n"),
        ("end", "recipe", None, "</recipe>")
    ]
    assert tokens == expected


def test_partial_xml_chunk(tokenizer):
    """Test tokenization of partial XML content"""
    chunk = "ingredient><quantity>1</quantity>"
    tokens = tokenizer.tokenize(chunk)
    
    expected = [
        ("text", None, "ingredient", "ingredient"),
        ("start", "quantity", None, "<quantity>"),
        ("text", None, "1", "1"),
        ("end", "quantity", None, "</quantity>")
    ]
    assert tokens == expected


def test_empty_chunk(tokenizer):
    """Test tokenization of empty chunk"""
    chunk = ""
    tokens = tokenizer.tokenize(chunk)
    assert tokens == []


def test_self_closing_tags(tokenizer):
    """Test tokenization of self-closing tags"""
    chunk = "<br/><hr/>"
    tokens = tokenizer.tokenize(chunk)
    
    expected = [
        ("start", "br", None, "<br/>"),
        ("start", "hr", None, "<hr/>")
    ]
    assert tokens == expected