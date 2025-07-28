import re
from typing import List, Optional, Tuple

from utils.logger import Logger

logger = Logger("xml_chunk_tokenizer", level="WARNING")


class XMLChunkTokenizer:
    """
    Tokenizes XML-like text into a sequence of structured tokens.

    This tokenizer breaks up a chunk of XML or XML-like text into a list of tokens,
    where each token is a tuple: (token_type, tag_name, text_content, raw_string)

    Token structure:
    - token_type: 'start' for start tags, 'end' for end tags, 'text' for text content
    - tag_name: the name of the tag (for tags), or None for text content
    - text_content: the text content (for text tokens), or None for tag tokens
    - raw_string: the exact string matched from the input

    This tokenizer is designed to be robust to malformed or incomplete XML, making it
    suitable for streaming or chunked parsing scenarios where the input may not be a
    complete or valid XML document. It preserves all content, including whitespace and
    newlines, as text tokens, allowing higher-level logic to reconstruct or process
    the structure as needed.

    Note: Currently, this tokenizer does not parse XML attributes. Future versions
    may include support for extracting and processing tag attributes (e.g.,
    <tag attr="value"> would be enhanced to capture attribute information).

    Examples:
        >>> tokenizer = XMLChunkTokenizer()
        >>> tokens = tokenizer.tokenize("<name>Test Recipe</name>")
        >>> tokens
        [('start', 'name', None, '<name>'), ('text', None, 'Test Recipe', 'Test Recipe'), ('end', 'name', None, '</name>')]
    """

    def __init__(self):
        """
        Initialize the XML chunk tokenizer.

        Sets up the regex pattern to match start/end tags and text between tags.
        The pattern captures:
        - Start tags: <tag_name>
        - End tags: </tag_name>
        - Text content: any content not enclosed in angle brackets
        """
        # Regex pattern to match start/end tags and text between tags
        self.pattern = re.compile(r"<(/?)(\w+)[^<>]*?>|([^<>]+)")

    def tokenize(self, chunk: str) -> List[Tuple[str, str, Optional[str], str]]:
        """
        Tokenize a chunk of XML-like text into a list of tokens.

        This method processes the input chunk and returns a list of structured tokens.
        Each token represents either an XML tag (start or end) or text content.

        Args:
            chunk: The XML chunk to tokenize

        Returns:
            A list of tuples, where each tuple contains:
            - token_type (str): 'start', 'end', or 'text'
            - tag_name (str): The tag name for tag tokens, or None for text tokens
            - text_content (Optional[str]): The text content for text tokens, or None for tag tokens
            - raw_string (str): The exact string matched from the input

        Examples:
            >>> tokenizer = XMLChunkTokenizer()
            >>> tokenizer.tokenize("<recipe><name>Test</name></recipe>")
            [
                ('start', 'recipe', None, '<recipe>'),
                ('start', 'name', None, '<name>'),
                ('text', None, 'Test', 'Test'),
                ('end', 'name', None, '</name>'),
                ('end', 'recipe', None, '</recipe>')
            ]
        """
        # Split the input into raw tokens: tags or text
        raw_tokens = re.findall(r"<[^<>]+>|[^<>]+", chunk)
        tokens = []
        for raw in raw_tokens:
            match = self.pattern.match(raw)
            if match:
                if match.group(3):  # Text content (not inside < >)
                    tokens.append(("text", None, match.group(3), raw))
                else:
                    is_end = bool(match.group(1))  # '/' means end tag
                    tag = match.group(2)
                    tokens.append(("end" if is_end else "start", tag, None, raw))
        return tokens
