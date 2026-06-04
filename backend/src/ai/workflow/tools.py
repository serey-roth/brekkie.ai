import os
from typing import Annotated, Any

from ai.workflow.prompts import create_recipe_prompt
from langchain_core.messages.ai import AIMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI


@tool(name_or_callable="create_recipe")
async def create_recipe(
    idea: Annotated[
        str,
        "What the user wants - could be a specifc request (vegan coq au vin for two), a mood-based idea (something cozy and comforting), or a general vibe (a meal for a special occasion)",
    ],
    context: Annotated[
        str,
        "User's constraints and situation - could be dietary needs, time limits, skill level, equipment, occasion, etc.",
    ],
) -> Any:
    """
    Create personalized recipes based on what the user wants and their current situation.

    Use when:
    - User directly asks for a recipe
    - They agree to a recipe suggestion
    - They give you ingredients, constraints, or just a general mood/direction

    Returns detailed recipes that are feasible and personalized to the user's request and situation.
    """
    create_recipe_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        api_key=os.getenv("GOOGLE_API_KEY"),
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(create_recipe_prompt),
            HumanMessagePromptTemplate.from_template(
                "Recipe idea: {idea}\n\nUser context: {context}"
            ),
        ]
    )

    result = await create_recipe_llm.ainvoke(prompt.format_messages(idea=idea, context=context))
    content = str(result.content).strip()

    if isinstance(result, AIMessage):
        metadata = result.response_metadata
        usage_metadata = result.usage_metadata
    else:
        metadata = getattr(result, "response_metadata", None)
        usage_metadata = getattr(result, "usage_metadata", None)

    return {
        "content": content,
        "response_metadata": metadata,
        "usage_metadata": usage_metadata,
    }


TOOLS = [create_recipe]

__all__ = ["TOOLS"]
