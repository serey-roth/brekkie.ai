from typing import Optional, Tuple

from utils.logger import Logger

logger = Logger("xml_tag_tracker", level="WARNING")


class XMLTagTracker:
    """
    Tracks and manages nested XML tags during streaming parsing.

    This class maintains a stack of open XML tags and handles the completion
    of nested structures. It's designed to work with streaming XML parsers
    where tags may be opened and closed in arbitrary order across multiple
    chunks of input.

    The tracker keeps track of known tags and their associated content buffers,
    automatically completing child tags when their parent tags are closed.
    This ensures that nested XML structures are properly handled even when
    they span multiple chunks or are malformed.

    Attributes:
        known_tags (set): Set of tag names that this tracker should process
        stack (list): Stack of open tags, each containing tag name and buffer

    Examples:
        >>> tracker = XMLTagTracker(known_tags={"name", "ingredient"})
        >>> tracker.track("start", "name", None, "<name>")
        None  # Tag opened, buffered
        >>> tracker.track("text", None, "Test Recipe", "Test Recipe")
        None  # Text added to buffer
        >>> tracker.track("end", "name", None, "</name>")
        [("name", "<name>Test Recipe</name>")]  # Tag completed
    """

    def __init__(self, known_tags):
        """
        Initialize the XML tracker with a set of known tags.

        Args:
            known_tags (set): Set of tag names that should be tracked and processed
        """
        self.known_tags = set(known_tags)
        self.stack = []  # Each item: {'tag': str, 'buffer': str}

    def track(
        self, typ: str, tag: str, text: Optional[str], raw: str
    ) -> Optional[list[Tuple[str, str]]]:
        """
        Process an XML token and track tag state changes.

        This method handles start tags, end tags, and text content. It maintains
        the tag stack and returns completed tag structures when tags are closed.

        Args:
            typ (str): Token type - 'start', 'end', or 'text'
            tag (str): Tag name for start/end tokens, or None for text tokens
            text (Optional[str]): Text content for text tokens, or None for tag tokens
            raw (str): The raw string content of the token

        Returns:
            Optional[list[Tuple[str, str]]]: List of (tag_name, completed_xml) tuples
                for completed tags, or None if no tags were completed

        Examples:
            >>> tracker = MultiTagXMLTracker({"name"})
            >>> tracker.track("start", "name", None, "<name>")
            None
            >>> tracker.track("end", "name", None, "</name>")
            [("name", "<name></name>")]
        """
        if typ == "start":
            return self._handle_start(tag, raw)
        elif typ == "text":
            return self._handle_text(raw)
        elif typ == "end":
            return self._handle_end(tag, raw)
        return None

    def _handle_start(self, tag, raw) -> None:
        """
        Handle a start tag by pushing it onto the stack.

        Args:
            tag (str): The tag name
            raw (str): The raw XML string for the start tag

        Returns:
            None: Start tags are buffered and don't produce immediate results
        """
        if tag in self.known_tags:
            self.stack.append({"tag": tag, "buffer": raw})
        return None

    def _handle_text(self, raw) -> None:
        """
        Handle text content by appending it to the current tag's buffer.

        Args:
            raw (str): The raw text content

        Returns:
            None: Text is buffered and doesn't produce immediate results
        """
        if self.stack:
            self.stack[-1]["buffer"] += raw
        return None

    def _handle_end(self, tag, raw) -> Optional[list[Tuple[str, str]]]:
        """
        Handle an end tag by completing the matching tag and its children.

        When an end tag is encountered, this method:
        1. Finds the matching start tag in the stack
        2. Completes any unclosed child tags above it
        3. Adds the end tag to the completed buffer
        4. Returns the completed XML structure

        Args:
            tag (str): The tag name being closed
            raw (str): The raw XML string for the end tag

        Returns:
            Optional[list[Tuple[str, str]]]: List of completed tag structures,
                or None if no matching start tag was found
        """
        # Find the matching tag in the stack (from the top)
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                completed = self.stack[i]
                # Complete any child tags and add their buffers to the parent
                child_results = self._complete_children(i)
                # Now add the closing tag to the parent buffer
                completed["buffer"] += raw
                # Pop all tags above and including the matched one
                self.stack = self.stack[:i]
                # If there's a parent, add this buffer to it
                if self.stack:
                    self.stack[-1]["buffer"] += completed["buffer"]
                # Return child results first, then the completed tag
                results = (
                    child_results + [(tag, completed["buffer"])]
                    if tag in self.known_tags
                    else child_results
                )
                return results if results else None
                break
        # If not found, ignore (malformed XML)
        return None

    def _complete_children(self, parent_index) -> list[Tuple[str, str]]:
        """
        Complete all child tags above the parent_index in the stack.

        This method automatically closes any unclosed child tags when their
        parent tag is being closed. It adds the completed child buffers to
        the parent buffer and returns results for known child tags.

        Args:
            parent_index (int): Index of the parent tag in the stack

        Returns:
            list[Tuple[str, str]]: List of (tag_name, completed_xml) for known child tags
        """
        child_results: list[Tuple[str, str]] = []
        for j in range(parent_index + 1, len(self.stack)):
            child_tag_info = self.stack[j]
            completed_child_buffer = child_tag_info["buffer"] + f"</{child_tag_info['tag']}>"
            # Only return results for known tags
            if child_tag_info["tag"] in self.known_tags:
                child_results.append((child_tag_info["tag"], completed_child_buffer))
            # Always add the completed child buffer to the parent buffer
            self.stack[parent_index]["buffer"] += completed_child_buffer
        return child_results

    def reset(self):
        """
        Reset the tracker state by clearing the tag stack.

        This method should be called when starting to parse a new XML document
        or when you want to clear the current parsing state.
        """
        self.stack = []
