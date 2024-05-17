"""Supabase session dependency."""

import os
from typing import Annotated
from fastapi import Depends, status, HTTPException
from supabase_py_async import AsyncClient, create_client
from httpx import HTTPStatusError
from gotrue import errors


async def init_supabase_client() -> AsyncClient:
    """Initialize a Supabase client."""
    return await create_client(
        supabase_key=os.getenv("SUPABASE_ANON_KEY"),
        supabase_url=os.getenv("SUPABASE_URL"),
    )


Session = Annotated[AsyncClient, Depends(init_supabase_client)]


async def get_user_session(session: Session, authorization: str) -> AsyncClient:
    """
    Returns a client authenticated using the provided user's JWT token

    Parameters:
        session (Session): the default anonymous session
        authorization (str): the JWT token for the user

    Returns:
        user_client (AsyncClient): a client instantiated with a session associated with the JWT token
    """

    authorized = True

    if authorization is None:
        authorized = False

    api_key: str = authorization.replace("Bearer ", "")

    try:
        user: None = await session.auth.get_user(api_key)

        if user is None:
            authorized = False
    except HTTPStatusError:
        authorized = False
    except errors.AuthApiError:
        authorized = False

    if not authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return await create_client(
        supabase_key=os.getenv("SUPABASE_ANON_KEY"),
        supabase_url=os.getenv("SUPABASE_URL"),
        access_token=api_key,
    )
