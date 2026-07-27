from uuid import uuid4

import asyncpg
from fastapi import APIRouter, HTTPException, status

from app.db import get_pool
from app.models import SignInRequest, SignUpRequest, SignUpResponse, TokenResponse
from app.repositories import projects as projects_repo
from app.repositories import users as users_repo
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sign-in", response_model=TokenResponse)
async def sign_in(payload: SignInRequest) -> TokenResponse:
    pool = get_pool()
    async with pool.acquire() as conn:
        user = await users_repo.get_by_email(conn, payload.email)

    if user is None or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    return TokenResponse(access_token=create_access_token(str(user["id"])))


@router.post("/sign-up", response_model=SignUpResponse)
async def sign_up(payload: SignUpRequest) -> SignUpResponse:
    pool = get_pool()
    async with pool.acquire() as conn, conn.transaction():
        user_id = uuid4()
        try:
            await users_repo.create(
                conn, user_id, payload.email, hash_password(payload.password)
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="a user with this email already exists",
            )

        await projects_repo.create(conn, uuid4(), f"{payload.email}'s project", user_id)
    return SignUpResponse(id=user_id, email=payload.email)
