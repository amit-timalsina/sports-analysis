import logging as logger
from typing import Annotated

import svcs
from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies.security import get_current_user, get_current_user_supabase_id
from auth.exceptions.exceptions import UserAlreadyExistsError, UserNotFoundError
from auth.repositories.user_repository import UserRepository
from auth.schemas.identity_provider import IdentityProvider
from auth.schemas.user import User as UserGet
from auth.schemas.user import UserBase, UserCreate, UserUpdate
from auth.schemas.user_identity import UserIdentityBase

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserGet)
async def create_user(
    user: UserBase,
    dep_container: svcs.fastapi.DepContainer,
    supabase_id: Annotated[str, Depends(get_current_user_supabase_id)],
) -> UserGet:
    """
    Create a new user.

    Args:
    ----
        user (UserCreate): The user data to create.

    Returns:
    -------
        User: The created user.

    Raises:
    ------
        UserAlreadyExistsError: If the user already exists.
        UserNotFoundError: If the user does not exist.

    """
    logger.debug("Creating user with supabase_id: %s", supabase_id)
    user_repository = await dep_container.aget(UserRepository)
    user_identity = UserIdentityBase(
        provider=IdentityProvider.SUPABASE,
        provider_user_id=supabase_id,
    )

    try:
        existing_user = await user_repository.read_by_identity(user_identity)
        # If the user already exists, throw an error
        if existing_user:
            raise UserAlreadyExistsError
    except UserNotFoundError:
        # Otherwise, create the user
        return await user_repository.create(
            UserCreate(
                **user.model_dump(),
                identities=[user_identity],
            ),
        )

    # If we reach this point, it means the user exists but we didn't raise an error
    # We should explicitly raise the error here
    raise UserAlreadyExistsError


@router.get("", response_model=UserGet)
async def read_user(
    current_user: Annotated[UserGet, Depends(get_current_user)],
) -> UserGet:
    """
    Read the current user.

    Returns
    -------
        User: The current user.

    Raises
    ------
        HTTPException: If the user is not found.

    """
    try:
        return current_user
    except UserNotFoundError as e:
        raise e.to_http_exception() from None


@router.put("", response_model=UserGet)
async def update_user(
    user: UserUpdate,
    dep_container: svcs.fastapi.DepContainer,
    current_user: Annotated[UserGet, Depends(get_current_user)],
) -> UserGet:
    """
    Update the current user.

    Args:
    ----
        user (UserUpdate): The updated user data.

    Returns:
    -------
        User: The updated user.

    Raises:
    ------
        HTTPException: If the user is not found or if there's an error during update.

    """
    try:
        repo = await dep_container.aget(UserRepository)
        return await repo.update(current_user.id, user)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail="User not found") from e


@router.delete("", response_model=UserGet)
async def delete_user(
    dep_container: svcs.fastapi.DepContainer,
    current_user: Annotated[UserGet, Depends(get_current_user)],
) -> UserGet:
    """
    Delete the current user.

    Returns
    -------
        User: The deleted user.

    Raises
    ------
        HTTPException: If the user is not found or if there's an error during deletion.

    """
    try:
        repo = await dep_container.aget(UserRepository)
        return await repo.delete(current_user.id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail="User not found") from e
