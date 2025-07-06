from uuid import uuid4
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Response
from datetime import datetime, timezone

from config.settings import get_settings

from api.deps import get_client_ip, get_service_container, get_access_token

from schemas.api_error import RateLimitError
from schemas.users import CreateUserParams, User, UserSignup, UserLogin
from schemas.user_access import UserAccessData
from schemas.threads import CreateThreadParams
from schemas.recipes import CreateRecipeParams
from schemas.messages import CreateMessageParams

from services.service_container import ServiceContainer

from utils.date_utils import to_utc_isostring
from utils.logger import Logger

logger = Logger("api.routes.auth")


async def _migrate_user_data(old_user_id: str, new_user_id: str, service_container: ServiceContainer):
    logger.info(f"Starting migration from old_user_id={old_user_id} to new_user_id={new_user_id}")
    try:
        async with service_container.db_transaction_maker() as db:
            threads = await service_container.thread_cache_service.get_threads(old_user_id)
            logger.info(f"Found {len(threads)} threads to migrate")
            if len(threads) > 0:
                thread_params = [
                    CreateThreadParams(
                        id=thread.id,
                        user_id=new_user_id,
                        created_at=datetime.fromisoformat(thread.created_at).replace(tzinfo=timezone.utc),
                        updated_at=datetime.fromisoformat(thread.updated_at).replace(tzinfo=timezone.utc),
                        resumed_at=datetime.fromisoformat(thread.resumed_at).replace(tzinfo=timezone.utc) if thread.resumed_at else None,
                        is_empty=thread.is_empty,
                        title=thread.title,
                        summary=thread.summary,
                        error_message=thread.error_message,
                    )
                    for thread in threads if thread.is_empty is False
                ]
                await service_container.thread_service.create_threads(db, thread_params)
                await service_container.thread_cache_service.delete_threads_by_user_id(old_user_id)
                logger.info(f"Successfully migrated {len(threads)} threads")
                
            recipes = await service_container.recipe_cache_service.get_recipes_by_user_id(old_user_id)
            logger.info(f"Found {len(recipes)} recipes to migrate")
            if len(recipes) > 0:
                recipe_params = [
                    CreateRecipeParams(
                        id=recipe.id,
                        user_id=new_user_id,
                        thread_id=recipe.thread_id,
                        created_at=datetime.fromisoformat(recipe.created_at).replace(tzinfo=timezone.utc),
                        updated_at=datetime.fromisoformat(recipe.updated_at).replace(tzinfo=timezone.utc),
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
                
            messages = await service_container.message_cache_service.get_messages_by_user_id(old_user_id)
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
                        created_at=datetime.fromisoformat(message.created_at).replace(tzinfo=timezone.utc),
                        updated_at=datetime.fromisoformat(message.updated_at).replace(tzinfo=timezone.utc),
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
                await service_container.message_cache_service.delete_messages_by_user_id(old_user_id)
                logger.info(f"Successfully migrated {len(messages)} messages")
        
        logger.info(f"Migration completed successfully from old_user_id={old_user_id} to new_user_id={new_user_id}")
    except Exception as e:
        logger.error(f"Error during migration from old_user_id={old_user_id} to new_user_id={new_user_id}: {e}")
        raise


router = APIRouter()

# TODO: Add email verification

@router.post("/login", response_model=UserAccessData)
async def login(
    response: Response,
    payload: UserLogin, 
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> UserAccessData:
    logger.debug(f"Login attempt for email: {payload.email}")
    
    try:
        user_service = service_container.user_service
        async with service_container.db_transaction_maker() as db:
            user = await user_service.get_user_by_email(db, payload.email)
            if user is None:
                logger.error(f"User with email {payload.email} not found")
                raise HTTPException(status_code=401, detail={"message": "User does not exist"})
                
            if not await user_service.verify_password(db, user.id, payload.password):
                logger.error(f"Invalid password for user {payload.email}")
                raise HTTPException(status_code=401, detail={"message": "Invalid credentials"})
        
            user_message_count = await service_container.message_service.count_total_messages_sent_by_user(db, user.id)
            
            timestamp = datetime.now(timezone.utc)
            
            new_access_data = await service_container.user_access_cache_service.create_user_access(
                access_token=str(uuid4()),
                user_id=user.id,
                email=user.email,
                name=user.name,
                is_authenticated=True,
                user_message_count=user_message_count,
                created_at=to_utc_isostring(timestamp),
                updated_at=to_utc_isostring(timestamp),
            )
            
            settings = get_settings()
            response.delete_cookie(settings.cookie_name) # Delete the old cookie
            response.set_cookie(
                settings.cookie_name,
                new_access_data.access_token,
                secure=settings.cookie_secure,
                httponly=settings.cookie_httponly,
                max_age=settings.cookie_max_age,
                samesite=settings.cookie_samesite,
            )

            logger.info(f"User {user.id} ({user.email}) logged in successfully")
            return new_access_data
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})
   
   
@router.post("/signup", response_model=UserAccessData)
async def signup(
    response: Response,
    payload: UserSignup, 
    service_container: Annotated[ServiceContainer, Depends(get_service_container)], 
    background_tasks: BackgroundTasks,
    access_token: Annotated[str | None, Depends(get_access_token)] = None,
) -> UserAccessData:
    logger.debug(f"Signup attempt for email: {payload.email}")
    
    try:
        if not access_token:
            raise HTTPException(status_code=401, detail={"message": "Missing access token"})

        user_access_data = await service_container.user_access_cache_service.get_user_access(access_token)
        if user_access_data is None:
            raise HTTPException(status_code=401, detail={"message": "Access token not found"})
        
        if user_access_data.is_authenticated:
            return user_access_data
        
        old_user_id = user_access_data.user_id
        
        timestamp = datetime.now(timezone.utc)
        
        user_service = service_container.user_service
        async with service_container.db_transaction_maker() as db:
            existing = await user_service.get_user_by_email(db, payload.email)
            if existing:
                logger.error(f"User with email {payload.email} already exists")
                raise HTTPException(status_code=400, detail={"message": "User already exists"})
        
            user = await user_service.create_user(
                db, 
                CreateUserParams(
                    id=str(uuid4()),
                    created_at=timestamp,
                    updated_at=timestamp,
                    email=payload.email,
                    name=payload.name,
                    password=payload.password
                )
            )

            old_user_message_count = await service_container.message_cache_service.count_total_messages_sent_by_user(old_user_id)
            
            new_access_data = await service_container.user_access_cache_service.create_user_access(
                access_token=str(uuid4()),
                user_id=user.id,
                email=user.email,
                name=user.name,
                is_authenticated=True,
                user_message_count=old_user_message_count,
                created_at=to_utc_isostring(timestamp),
                updated_at=to_utc_isostring(timestamp),
            )
            
            await service_container.user_access_cache_service.revoke_access(access_token)
            
            settings = get_settings()
            response.set_cookie(
                settings.cookie_name,
                new_access_data.access_token,
                secure=settings.get_cookie_secure(),
                samesite=settings.cookie_samesite,
                max_age=settings.cookie_max_age,
                httponly=settings.get_cookie_httponly(),
                path=settings.cookie_path,
            )
            
            logger.info(f"User {user.id} ({user.email}) signed up successfully")
            background_tasks.add_task(_migrate_user_data, old_user_id, user.id, service_container)

            return new_access_data
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error during signup: {e}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.post("/logout", response_model=UserAccessData)
async def logout(
    response: Response,
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    ip_address: Annotated[str, Depends(get_client_ip)],
    access_token: Annotated[str | None, Depends(get_access_token)] = None,
) -> UserAccessData:
    try:
        if not access_token:
            raise HTTPException(status_code=401, detail={"message": "Missing access token"})
        
        user_access_data = await service_container.user_access_cache_service.get_user_access(access_token)
        if user_access_data is None:
            raise HTTPException(status_code=401, detail={"message": "Access token not found"})
        
        if not user_access_data.is_authenticated:
            raise HTTPException(status_code=400, detail={"message": "User not authenticated"})
        
        user_access_cache_service = service_container.user_access_cache_service
        await user_access_cache_service.revoke_access(access_token)
        
        # TODO: This might change when we add OAuth
        new_access_data = await service_container.anonymous_access_service.get_or_create_user_access(ip_address, None)
        
        settings = get_settings()
        response.delete_cookie(settings.cookie_name) # Delete the old cookie
        response.set_cookie(
            settings.cookie_name,
            new_access_data.access_token,
            secure=settings.cookie_secure,
            httponly=settings.cookie_httponly,
            max_age=settings.cookie_max_age,
            samesite=settings.cookie_samesite,
        )
        
        logger.info(f"User {user_access_data.user_id} ({user_access_data.email}) logged out successfully")
        return new_access_data
    
    except RateLimitError:
        raise HTTPException(status_code=429, detail={"message": "Too many anonymous requests from this device. Please try again later."})
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error during logout: {e}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})
