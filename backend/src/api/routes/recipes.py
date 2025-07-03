from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException

from api.deps import get_service_container

from schemas.recipes import UserRecipe
from schemas.user_access import UserAccessData

from services.service_container import ServiceContainer

from utils.logger import Logger

logger = Logger("api.routes.recipes")


def _extract_access_token(access_token: Annotated[str | None, Header()] = None) -> str | None:
    if not access_token:
        return None
    if not access_token.startswith("Bearer "):
        return None
    access_token = access_token.replace("Bearer ", "").strip()
    if not access_token:
        return None
    return access_token


async def _validate_access_token(access_token: str, service_container: ServiceContainer) -> UserAccessData:
    user_access_cache_service = service_container.user_access_cache_service
    user_access_data = await user_access_cache_service.get_user_access(access_token)
    return user_access_data


router = APIRouter()

# TODO: Add pagination

@router.get("/recipes")
async def get_user_recipes(
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    authorization: Annotated[str | None, Header()] = None,
) -> list[UserRecipe]:
    access_token = _extract_access_token(authorization)
    user_access_data = await _validate_access_token(access_token, service_container)
    if not user_access_data:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if user_access_data.is_authenticated:
        recipe_service = service_container.recipe_service
        with service_container.db_transaction_maker() as db:
            recipes = await recipe_service.get_user_recipes(db, user_access_data.user_id)
            return recipes
    else:
        recipe_cache_service = service_container.recipe_cache_service
        recipes = await recipe_cache_service.get_recipes_by_user_id(user_access_data.user_id)
        return recipes