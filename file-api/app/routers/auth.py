from fastapi import APIRouter, HTTPException, status

from app.db import get_pool
from app.models import LoginRequest, TokenResponse
from app.repositories import users as users_repo
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    pool = get_pool()
    async with pool.acquire() as conn:
        user = await users_repo.get_by_email(conn, payload.email)

    if user is None or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    return TokenResponse(access_token=create_access_token(str(user["id"])))
