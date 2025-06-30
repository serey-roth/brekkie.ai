import re

from utils.logger import Logger

logger = Logger("xml_chunk_patcher", level="WARNING")


class XMLChunkPatcher:
    """
    Patches incomplete XML chunks by buffering fragments and joining them when complete.
    
    This class handles cases where XML tags are split across multiple chunks during streaming
    or chunked parsing scenarios. It maintains an internal buffer to accumulate incomplete
    XML fragments and joins them with subsequent chunks when they become complete.
    
    Examples of handled cases:
    - Chunk 1: "<recipe"
    - Chunk 2: "><name>Test Recipe</name>"
    
    The patcher will buffer the first chunk and join it with the second to create:
    - "<recipe><name>Test Recipe</name>"
    
    This is particularly useful for streaming XML parsers where the input arrives
    in arbitrary chunks and tags may be split across chunk boundaries.
    """
    
    def __init__(self):
        """Initialize the XML chunk patcher with an empty buffer."""
        self.buffer = ""
    
    def patch(self, chunk: str) -> str | None:
        """
        Patch a chunk with any buffered incomplete content.
        
        This method processes incoming chunks by:
        1. Joining the current chunk with any buffered incomplete content
        2. Detecting if the current chunk ends with an incomplete XML tag
        3. Buffering incomplete tags for later processing
        4. Returning complete, processable XML fragments
        
        Args:
            chunk: The XML chunk to process
            
        Returns:
            The patched chunk if it's complete and processable, or None if the
            chunk was buffered for later processing. An empty string is returned
            if the chunk was buffered and there was no complete content to return.
            
        Examples:
            >>> patcher = XMLChunkPatcher()
            >>> patcher.patch("<recipe")
            None  # Buffered, no complete content
            >>> patcher.patch("><name>Test</name>")
            "<recipe><name>Test</name>"  # Complete, returned
        """
        logger.debug(f"Patching chunk: '{chunk}'")
        logger.debug(f"Current buffer: '{self.buffer}'")
        
        # If we have a buffer and this chunk might complete it
        if self.buffer and not self.buffer.endswith(">"):
            # Join buffer with current chunk
            chunk = self.buffer + chunk
            self.buffer = ""
            logger.debug(f"Joined with buffer: '{chunk}'")
        
        # If the chunk ends with a partial tag (opening or closing), buffer it
        # Look for incomplete opening tags: <tag_name
        # Look for incomplete closing tags: </tag_name
        m = re.search(r"(</?[a-zA-Z0-9_:-]*$)", chunk)
        if m:
            complete_part = chunk[:m.start()]
            incomplete_part = chunk[m.start():]
            logger.debug(f"Trailing partial tag detected. Buffering: '{incomplete_part}'")
            self.buffer = incomplete_part
            result = complete_part if complete_part else None
            logger.debug(f"Returning: '{result}'")
            return result
        
        # This is a complete chunk, return it as-is
        logger.debug(f"Returning complete chunk: '{chunk}'")
        return chunk
    
    def flush(self) -> str:
        """
        Flush any remaining buffered content.
        
        This method should be called when the stream is complete to retrieve
        any remaining buffered content that hasn't been processed yet.
        
        Returns:
            The remaining buffered content as a string, or an empty string
            if the buffer is empty.
            
        Examples:
            >>> patcher = XMLChunkPatcher()
            >>> patcher.patch("<recipe")
            None
            >>> patcher.flush()
            "<recipe"  # Returns buffered content
        """
        content = self.buffer
        self.buffer = ""
        return content
        
    def reset(self):
        self.buffer = ""
