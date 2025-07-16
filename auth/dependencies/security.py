from typing import Annotated

import svcs
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.repositories.user_repository import UserRepository
from auth.schemas.identity_provider import IdentityProvider
from auth.schemas.user import User
from auth.schemas.user_identity import UserIdentityBase
from auth.services.supabase import AuthSupabaseService
from logger import get_logger

logger = get_logger(__name__)

security = HTTPBearer()


async def get_current_user_supabase_id(
    services: svcs.fastapi.DepContainer,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """Get the current user's Supabase ID from the token."""
    supabase_service = await services.aget(AuthSupabaseService)
    return supabase_service.get_current_user_supabase_id(token.credentials)


async def get_current_user(
    services: svcs.fastapi.DepContainer,
    supabase_id: Annotated[str, Depends(get_current_user_supabase_id)],
) -> User:
    """Get the current user from the Supabase ID."""
    user_repository = await services.aget(UserRepository)
    return await user_repository.read_by_identity(
        UserIdentityBase(
            provider=IdentityProvider.SUPABASE,
            provider_user_id=supabase_id,
        ),
    )
