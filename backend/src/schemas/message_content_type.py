from enum import Enum


class MessageContentType(str, Enum):
    text = "text"
    recipe = "recipe"
    tool = "tool"
