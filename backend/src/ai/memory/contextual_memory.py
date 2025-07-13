from typing import Annotated

from pydantic import BaseModel, Field


class ContextualMemory(BaseModel):
    """Stores specific experiences, preferences, and discoveries shared by the user.

    Each memory represents a single fact or experience that can be used to:
    - Track the user's journey and learning
    - Remember specific preferences and discoveries
    - Build connections between different experiences
    - Provide personalized recommendations

    Examples:
        # Food-related memory
        {
            "entity": "user",
            "experience": "enjoyed",
            "topic": "homemade pasta",
            "context": "first time making from scratch, found it challenging but rewarding"
        }

        # Cooking skill memory
        {
            "entity": "user",
            "experience": "learned",
            "topic": "knife skills",
            "context": "practiced during meal prep, improved chopping speed"
        }

        # General preference memory
        {
            "entity": "user",
            "experience": "prefers",
            "topic": "quick recipes",
            "context": "busy work schedule, limited cooking time"
        }
    """

    entity: Annotated[
        str, Field(description="Who/what is this memory about (usually 'user' or specific entity)")
    ]  # Who/what is this memory about (usually "user" or specific entity)
    experience: Annotated[
        str,
        Field(
            description="What happened or what's the relationship (enjoyed, discovered, learned, etc.)"
        ),
    ]  # What happened or what's the relationship (enjoyed, discovered, learned, etc.)
    topic: Annotated[
        str, Field(description="The specific subject, item, or experience being remembered")
    ]  # The specific subject, item, or experience being remembered
    context: Annotated[
        str | None,
        Field(description="Additional details about when/where/why this memory was formed"),
    ]  # Additional details about when/where/why this memory was formed


contextual_memory_namespace = ("brekkie", "{user_id}", "contextual_memory")
