from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from api.deps import decode_supabase_jwt, get_jwt_token, get_service_container, get_settings
from config.settings import Settings
from fastapi import APIRouter, Depends, HTTPException
from services.service_container import ServiceContainer
from schemas.users import CreateUserParams, UpdateUserParams
from utils.logger import Logger

logger = Logger("api.routes.auth")

router = APIRouter()


@router.post("/verify-jwt")
async def verify(
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    settings: Annotated[Settings, Depends(get_settings)],
    jwt_token: Annotated[str | None, Depends(get_jwt_token)] = None,
):
    if not settings.is_auth_enabled():
        raise HTTPException(status_code=403, detail={"message": "Auth is disabled"})

    if jwt_token is None:
        raise HTTPException(status_code=401, detail={"message": "Missing JWT token"})

    payload = decode_supabase_jwt(jwt_token, settings)
    external_id = payload.get("sub")
    email = payload.get("email")
    name = payload.get("user_metadata", {}).get("name")

    if not external_id:
        raise HTTPException(status_code=401, detail={"message": "Invalid token: missing user ID"})

    timestamp = datetime.now(timezone.utc)

    async with service_container.db_transaction_maker() as db:  # type: ignore
        try:
            user = await service_container.user_service.get_user_by_external_id_or_email(
                db, external_id, email
            )
            if user is None:
                user = await service_container.user_service.create_user(
                    db,
                    CreateUserParams(
                        id=str(uuid4()),
                        external_id=external_id,
                        created_at=timestamp,
                        updated_at=timestamp,
                        last_signed_in_at=timestamp,
                        email=email,
                        name=name,
                    ),
                )
            else:
                user = await service_container.user_service.update_user(
                    db,
                    UpdateUserParams(
                        id=user.id,
                        external_id=external_id,
                        updated_at=timestamp,
                        last_signed_in_at=timestamp,
                        email=email,
                        name=name,
                    ),
                )
        except Exception as e:
            logger.error(f"Error upserting user: {e}")
            raise HTTPException(status_code=500, detail={"message": "Token verification failed"})

    return {"user_id": user.id}
