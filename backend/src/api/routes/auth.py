import json
import ssl
from datetime import datetime, timezone
from typing import Annotated
from urllib.request import urlopen
from uuid import uuid4

from api.deps import (
    get_jwt_token,
    get_client_ip,
    get_service_container,
    get_settings,
)

from config.settings import Settings

from fastapi import APIRouter, Depends, HTTPException, Response
from jose import JWTError, jwt
from jose.jwk import construct as jwk_construct

from services.service_container import ServiceContainer

from schemas.messages import CountMessagesParams
from schemas.message_role import MessageRole
from schemas.users import CreateUserParams, UpdateUserParams

from utils.date_utils import to_utc_isostring
from utils.logger import Logger

logger = Logger("api.routes.auth")


router = APIRouter()    

@router.post("/verify-jwt")
async def verify(
    response: Response,
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    settings: Annotated[Settings, Depends(get_settings)],
    ip_address: Annotated[str, Depends(get_client_ip)],
    jwt_token: Annotated[str | None, Depends(get_jwt_token)] = None,
):
    if not settings.is_auth_enabled():
        raise HTTPException(status_code=403, detail={"message": "Auth is disabled"})
    
    if jwt_token is None:
        logger.error("Missing JWT token")
        raise HTTPException(status_code=401, detail={"message": "Missing JWT token"})

    try:
        supabase_url = settings.supabase_url

        # Handle SSL certificate verification based on environment
        ssl_context = None
        if settings.is_development():
            # For development, disable SSL verification to avoid certificate issues
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            jsonurl = urlopen(supabase_url+"/auth/v1/.well-known/jwks.json", context=ssl_context)
        else:
            # For production/staging, use proper SSL verification
            jsonurl = urlopen(supabase_url+"/auth/v1/.well-known/jwks.json")
            
        logger.info(f"Supabase auth URL: {supabase_url}")
        jwks_response = jsonurl.read()
        logger.info(f"Supabase auth jwks: {jwks_response}")
            
        jwks = json.loads(jwks_response)
        unverified_header = jwt.get_unverified_header(jwt_token)
        logger.info(f"JWT header: {unverified_header}")
        public_key = None
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                public_key = jwk_construct(key)
                break
                
        if not public_key:
            logger.error(f"No matching key found for kid: {unverified_header.get('kid')}")
            raise HTTPException(status_code=401, detail={"message": "Invalid token: no matching key"})
            
        if public_key:
            try:
                payload = jwt.decode(
                    jwt_token,
                    public_key,
                    algorithms=["ES256"],
                    audience="authenticated",
                    issuer=supabase_url + "/auth/v1"
                )
            except JWTError as e:
                logger.error(f"JWTError: Invalid token {jwt_token}")
                raise HTTPException(status_code=401, detail={"message": "Invalid token"})
            
            logger.info(f"Supabase token verified successfully for user: {payload}")
            
            # Extract user ID from Supabase payload
            supabase_user_id = payload.get("sub")  # This is the unique Supabase user ID
            expires_at = int(payload.get("exp", 0))
            email = payload.get("email")
            name = payload.get("user_metadata", {}).get("name")
            
            logger.info(f"Supabase user payload: {payload}")
                    
            if supabase_user_id is None:
                raise HTTPException(status_code=400, detail={"message": "Invalid token: missing user ID"})
            
            timestamp = datetime.now(timezone.utc)
            current_message_count = 0
            
            async with service_container.db_transaction_maker() as db: # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
                try:
                    user = await service_container.user_service.get_user_by_external_id_or_email(db, supabase_user_id, email)
                    
                    if user is None:
                        user = await service_container.user_service.create_user(db, CreateUserParams(
                            id=str(uuid4()), 
                            external_id=supabase_user_id,
                            created_at=timestamp,
                            updated_at=timestamp,
                            last_signed_in_at=timestamp,
                            email=email,
                            name=name
                        ))
                    else:
                        user = await service_container.user_service.update_user(db, UpdateUserParams(
                            id=user.id,
                            external_id=supabase_user_id, # even if external_id is the Auth0 ID, we need to update the user with the Supabase ID
                            updated_at=timestamp,
                            last_signed_in_at=timestamp,
                            email=email,
                            name=name
                        ))
                        current_message_count = await service_container.message_service.count_messages(db, CountMessagesParams(user_id=user.id, role=MessageRole.user))
                
                except Exception as e:
                    logger.error(f"Error verifying Supabase token: {e}")
                    raise HTTPException(status_code=500, detail={"message": "Token verification failed"})

            ttl = int(expires_at) - int(timestamp.timestamp()) if expires_at is not None else None
            if ttl is not None and ttl < 0:
                ttl = None
                
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
            
            return current_user_access
        
        logger.error(f"JWTError: Invalid token {jwt_token}")
        raise HTTPException(status_code=401, detail={"message": "Invalid token"})
        
    except JWTError:
        logger.error(f"JWTError: Invalid token {jwt_token}")
        raise HTTPException(status_code=401, detail={"message": "Invalid token"})
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logger.error(f"Error verifying Supabase token: {e}")
        raise HTTPException(status_code=500, detail={"message": "Token verification failed"})