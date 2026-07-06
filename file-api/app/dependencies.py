from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.db import get_pool
from app.repositories import projects as projects_repo
from app.repositories import users as users_repo
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
    )
    try:
        user_id = UUID(decode_access_token(token))
    except (jwt.PyJWTError, ValueError):
        raise credentials_error

    pool = get_pool()
    async with pool.acquire() as conn:
        user = await users_repo.get_by_id(conn, user_id)
    if user is None:
        raise credentials_error
    return user


async def get_current_project(user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        project = await projects_repo.get_by_owner(conn, user["id"])
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project
