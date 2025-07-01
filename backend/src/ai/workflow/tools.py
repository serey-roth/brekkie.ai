import os
from typing import Annotated, Any

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch

from ai.workflow.prompts import search_prompt, create_recipe_prompt

# TODO: Use web search instead of Gemini, and maybe real time/geolocation search
@tool(name_or_callable="search")
async def search(query: Annotated[str, "What the user mentioned that needs lookup - places, people, dishes, cultural items, technical terms, media references, current events, trends, or any unfamiliar concept"]) -> str:
    """
    Look up information the user mentioned to provide context for responses.
    
    Use when the user references:
    - Specific places, people, dishes, or cultural items
    - Technical terms or unfamiliar concepts
    - Media references (movies, books, songs, shows)
    - Current events or trends they mention
    
    Returns factual information to inform appropriate responses.
    """
    search_llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.7,
        api_key=os.getenv("GOOGLE_API_KEY"),
        disable_streaming=True
    )
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(search_prompt),
        HumanMessagePromptTemplate.from_template("Query: {query}")
    ])
        
    chain = prompt | search_llm
    result = await chain.ainvoke({"query": query})
    return result.content.strip()


tavily_search = TavilySearch(
    max_results=3,
    topic="general",
    include_answer=True,
    include_raw_content=False,
    time_range="year",
    search_depth="advanced",
    api_key=os.getenv("TAVILY_API_KEY"),
)

@tool(name_or_callable="create_recipe")
async def create_recipe(
    idea: Annotated[str, "What the user wants - could be a specifc request (vegan coq au vin for two), a mood-based idea (something cozy and comforting), or a general vibe (a meal for a special occasion)"],  
    context: Annotated[str, "User's constraints and situation - could be dietary needs, time limits, skill level, equipment, occasion, etc."]
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
        model="gemini-2.5-flash-preview-05-20",
        temperature=0.7,
        api_key=os.getenv("GOOGLE_API_KEY"),
    )

    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(create_recipe_prompt),
        HumanMessagePromptTemplate.from_template("Recipe idea: {idea}\n\nUser context: {context}"),
    ])
    
    chain = prompt | create_recipe_llm
    result = await chain.ainvoke({"idea": idea, "context": context})
    return {"content": result.content.strip(), "response_metadata": result.response_metadata, "usage_metadata": result.usage_metadata}


# manage_contextual_memory = create_manage_memory_tool(
#     name="manage_contextual_memory",
#     namespace=contextual_memory_namespace,
#     instructions="Proactively call this tool when you:\n\n"
#     "1. Identify a new USER preference or behavior pattern.\n"
#     "2. Receive an explicit USER request to remember something or otherwise alter your behavior.\n"
#     "3. Are working and want to record important context or observations.\n"
#     "4. Identify that an existing MEMORY is incorrect or outdated.\n"
#     "5. Learn about USER's constraints, requirements, or limitations.\n"
#     "6. Discover USER's schedule, timing preferences, or practical needs.\n"
#     "7. Note USER's feedback, including likes, dislikes, and modifications made.\n",
#     schema=ContextualMemory,
#     actions_permitted=("create", "update", "delete")
# )

# search_contextual_memory = create_search_memory_tool(
#     name="search_contextual_memory",
#     namespace=contextual_memory_namespace,
#     instructions="Use this tool when you:\n"
#     "1. Need to search for prior preferences or behavior before suggesting something.\n"
#     "2. Want to confirm if a MEMORY exists before creating or updating one.\n"
#     "3. Personalize your responses based on the user's preferences and behavior patterns.\n"
#     "4. Need to check for constraints, likes, dislikes, or other preferences mentioned before."
# )


TOOLS = [create_recipe, tavily_search] 

__all__ = ["TOOLS"]