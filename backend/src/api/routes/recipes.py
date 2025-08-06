from typing import Annotated

from api.deps import get_access_token, get_service_container
from fastapi import APIRouter, Depends, HTTPException
from schemas.recipes import UserRecipe
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

    user_access = await service_container.user_access_cache_service.get_user_access(
        access_token
    )
    if user_access is None:
        raise HTTPException(status_code=401, detail={"message": "Access token not found"})

    if not user_access.is_authenticated:
        raise HTTPException(status_code=403, detail={"message": "Unauthorized"})
    
    recipe_service = service_container.recipe_service
    async with service_container.db_transaction_maker() as db:  # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
        return await recipe_service.get_user_recipes(db, user_access.user_id)
