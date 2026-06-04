from typing import Annotated

from api.deps import get_current_user_id, get_service_container
from fastapi import APIRouter, Depends
from schemas.recipes import UserRecipe
from services.service_container import ServiceContainer
from utils.logger import Logger

logger = Logger("api.routes.recipes")

router = APIRouter()


@router.get("/recipes")
async def get_user_recipes(
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> list[UserRecipe]:
    async with service_container.db_transaction_maker() as db:  # type: ignore
        return await service_container.recipe_service.get_user_recipes(db, user_id)
