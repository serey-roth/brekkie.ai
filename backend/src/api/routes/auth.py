import json
import ssl
from urllib.request import urlopen
from uuid import uuid4
from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Response
from jose import jwt, JWTError, jwk

from config.settings import Settings

from api.deps import get_client_ip, get_service_container, get_access_token, get_settings, get_auth0_token

from schemas.users import CreateUserParams
from schemas.user_access import UserAccess
from schemas.threads import CreateThreadParams
from schemas.recipes import CreateRecipeParams
from schemas.messages import CreateMessageParams

from services.service_container import ServiceContainer

from utils.date_utils import to_utc_isostring
from utils.logger import Logger

logger = Logger("api.routes.auth")


async def _migrate_user_data(
    old_user_id: str, new_user_id: str, service_container: ServiceContainer
):
    logger.info(f"Starting migration from old_user_id={old_user_id} to new_user_id={new_user_id}")
    try:
        async with service_container.db_transaction_maker() as db:  # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
            threads = await service_container.thread_cache_service.get_threads(old_user_id)
            logger.info(f"Found {len(threads)} threads to migrate")
            if len(threads) > 0:
                thread_params = [
                    CreateThreadParams(
                        id=thread.id,
                        user_id=new_user_id,
                        created_at=datetime.fromisoformat(thread.created_at).replace(
                            tzinfo=timezone.utc
                        ),
                        updated_at=datetime.fromisoformat(thread.updated_at).replace(
                            tzinfo=timezone.utc
                        ),
                        resumed_at=datetime.fromisoformat(thread.resumed_at).replace(
                            tzinfo=timezone.utc
                        )
                        if thread.resumed_at
                        else None,
                        is_empty=thread.is_empty,
                        title=thread.title,
                        summary=thread.summary,
                        error_message=thread.error_message,
                    )
                    for thread in threads
                    if thread.is_empty is False
                ]
                await service_container.thread_service.create_threads(db, thread_params)
                await service_container.thread_cache_service.delete_threads_by_user_id(old_user_id)
                logger.info(f"Successfully migrated {len(threads)} threads")

            recipes = await service_container.recipe_cache_service.get_recipes_by_user_id(
                old_user_id
            )
            logger.info(f"Found {len(recipes)} recipes to migrate")
            if len(recipes) > 0:
                recipe_params = [
                    CreateRecipeParams(
                        id=recipe.id,
                        user_id=new_user_id,
                        thread_id=recipe.thread_id,
                        created_at=datetime.fromisoformat(recipe.created_at).replace(
                            tzinfo=timezone.utc
                        ),
                        updated_at=datetime.fromisoformat(recipe.updated_at).replace(
                            tzinfo=timezone.utc
                        ),
                        name=recipe.name,
                        description=recipe.description,
                        ingredients=recipe.ingredients,
                        instructions=recipe.instructions,
                        categories=recipe.categories,
                        prep_time_minutes=recipe.prep_time_minutes,
                        cook_time_minutes=recipe.cook_time_minutes,
                        servings=recipe.servings,
                        chef_notes=recipe.chef_notes,
                        substitutions=recipe.substitutions,
                        equipment_alternatives=recipe.equipment_alternatives,
                        scaling_guidance=recipe.scaling_guidance,
                        storage_notes=recipe.storage_notes,
                        serving_suggestions=recipe.serving_suggestions,
                        make_ahead_tips=recipe.make_ahead_tips,
                        coordination_timeline=recipe.coordination_timeline,
                    )
                    for recipe in recipes
                ]
                await service_container.recipe_service.create_recipes(db, recipe_params)
                await service_container.recipe_cache_service.delete_recipes_by_user_id(old_user_id)
                logger.info(f"Successfully migrated {len(recipes)} recipes")

            messages = await service_container.message_cache_service.get_messages_by_user_id(
                old_user_id
            )
            logger.info(f"Found {len(messages)} messages to migrate")
            if len(messages) > 0:
                message_params = [
                    CreateMessageParams(
                        id=message.id,
                        user_id=new_user_id,
                        thread_id=message.thread_id,
                        role=message.role,
                        content_type=message.content_type,
                        text_content=message.text_content,
                        created_at=datetime.fromisoformat(message.created_at).replace(
                            tzinfo=timezone.utc
                        ),
                        updated_at=datetime.fromisoformat(message.updated_at).replace(
                            tzinfo=timezone.utc
                        ),
                        model_name=message.model_name,
                        input_tokens=message.input_tokens,
                        output_tokens=message.output_tokens,
                        tool_name=message.tool_name,
                        tool_input=message.tool_input,
                        tool_output=message.tool_output,
                        recipe_id=message.recipe_id,
                        is_recipe_generation_started=message.is_recipe_generation_started,
                        is_recipe_generation_completed=message.is_recipe_generation_completed,
                    )
                    for message in messages
                ]
                await service_container.message_service.create_messages(db, message_params)
                await service_container.message_cache_service.delete_messages_by_user_id(
                    old_user_id
                )
                logger.info(f"Successfully migrated {len(messages)} messages")

        logger.info(
            f"Migration completed successfully from old_user_id={old_user_id} to new_user_id={new_user_id}"
        )
    except Exception as e:
        logger.error(
            f"Error during migration from old_user_id={old_user_id} to new_user_id={new_user_id}: {e}"
        )
        raise


router = APIRouter()    

@router.post("/verify-token")
async def verify(
    response: Response,
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    settings: Annotated[Settings, Depends(get_settings)],
    background_tasks: BackgroundTasks,
    ip_address: Annotated[str, Depends(get_client_ip)],
    access_token: Annotated[str | None, Depends(get_access_token)] = None,
    auth0_token: Annotated[str | None, Depends(get_auth0_token)] = None,
):
    if not settings.is_auth_enabled():
        raise HTTPException(status_code=403, detail={"message": "Auth is disabled"})
    
    if auth0_token is None:
        logger.error(f"Missing auth0 token")
        raise HTTPException(status_code=401, detail={"message": "Missing auth0 token"})

    if access_token is None:
        logger.error(f"Missing access token")
        raise HTTPException(status_code=401, detail={"message": "Missing access token"})

    try:
        current_user_access = await service_container.user_access_cache_service.get_user_access(
            access_token
        )
        if current_user_access is None:
            raise HTTPException(status_code=401, detail={"message": "Access record not found"})
        
        auth0_domain = settings.auth0_domain
        auth0_audience = settings.auth0_audience
        
        # Handle SSL certificate verification based on environment
        if settings.is_development():
            # For development, disable SSL verification to avoid certificate issues
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            jsonurl = urlopen("https://"+auth0_domain+"/.well-known/jwks.json", context=ssl_context)
        else:
            # For production/staging, use proper SSL verification
            jsonurl = urlopen("https://"+auth0_domain+"/.well-known/jwks.json")
            
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(auth0_token)
        public_key = None
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                public_key = jwk.construct(key)
                break
                
        if public_key:
            payload = jwt.decode(
                auth0_token,
                public_key,
                algorithms=["RS256"],
                audience=auth0_audience,
                issuer="https://"+auth0_domain+"/"
            )
            
            logger.info(f"Auth0 token verified successfully for user: {payload}")
            
            # Extract user ID from Auth0 payload
            auth0_user_id = payload.get("sub")  # This is the unique Auth0 user ID
            expires_at = payload.get("exp")
            if auth0_user_id is None:
                raise HTTPException(status_code=400, detail={"message": "Invalid token: missing user ID"})
            
            old_user_id = current_user_access.user_id
            timestamp = datetime.now(timezone.utc)
            needs_migration = False
            
            async with service_container.db_transaction_maker() as db: # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
                user = await service_container.user_service.get_user_by_external_id(db, auth0_user_id)
                if user is None:
                    user = await service_container.user_service.create_user(db, CreateUserParams(
                        id=current_user_access.user_id,
                        external_id=auth0_user_id,
                        created_at=timestamp,
                        updated_at=timestamp
                    ))
                    
            if not current_user_access.is_authenticated:
                await service_container.user_access_cache_service.revoke_access(access_token)
                await service_container.anonymous_access_service.ip_rate_limiter.clear(ip_address)
                
                ttl = int(expires_at) - int(timestamp.timestamp()) if expires_at is not None else None
                if ttl is not None and ttl < 0:
                    ttl = None
                    
                current_message_count = await service_container.message_cache_service.count_total_messages_sent_by_user(current_user_access.user_id)
                current_user_access = await service_container.user_access_cache_service.create_user_access(
                    access_token=str(uuid4()),
                    user_id=user.id,
                    created_at=to_utc_isostring(timestamp),
                    updated_at=to_utc_isostring(timestamp),
                    is_authenticated=True,
                    ip_address=ip_address,
                    user_message_count=current_message_count,
                    ttl=ttl
                )
                

                response.set_cookie(
                    settings.cookie_name,
                    current_user_access.access_token,
                    secure=settings.get_cookie_secure(),
                    samesite=settings.cookie_samesite,  # type: ignore
                    max_age=settings.cookie_max_age,
                    httponly=settings.get_cookie_httponly(),
                    path=settings.cookie_path,
                )
                
                needs_migration = True
        
            if needs_migration:
                background_tasks.add_task(_migrate_user_data, old_user_id, user.id, service_container)
            
            return current_user_access
        
        logger.error(f"JWTError: Invalid token {auth0_token}")
        raise HTTPException(status_code=401, detail={"message": "Invalid token"})
        
    except JWTError as e:
        logger.error(f"JWTError: Invalid token {auth0_token}")
        raise HTTPException(status_code=401, detail={"message": "Invalid token"})
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logger.error(f"Error verifying Auth0 token: {e}")
        raise HTTPException(status_code=500, detail={"message": "Token verification failed"})
