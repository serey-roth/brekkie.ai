from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Cookie

from api.deps import get_service_container, get_access_token

from schemas.recipes import UserRecipe
from schemas.user_access import UserAccessData

from services.service_container import ServiceContainer

from utils.logger import Logger

logger = Logger("api.routes.recipes")

router = APIRouter()

# TODO: Add pagination

@router.get("/recipes")
async def get_user_recipes(
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    access_token: Annotated[str | None, Depends(get_access_token)] = None,
) -> list[UserRecipe]:
    if not access_token:
        raise HTTPException(status_code=401, detail={"message": "Missing access token"})
    
    user_access_data = await service_container.user_access_cache_service.get_user_access(access_token)
    if user_access_data is None:
        raise HTTPException(status_code=401, detail={"message": "Access token not found"})
    
    if user_access_data.is_authenticated:
        recipe_service = service_container.recipe_service
        async with service_container.db_transaction_maker() as db:
            recipes = await recipe_service.get_user_recipes(db, user_access_data.user_id)
            return recipes
    else:
        recipe_cache_service = service_container.recipe_cache_service
        recipes = await recipe_cache_service.get_recipes_by_user_id(user_access_data.user_id)
        return recipes