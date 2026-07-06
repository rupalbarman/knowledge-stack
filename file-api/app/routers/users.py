from fastapi import APIRouter, Depends

from app.db import get_pool
from app.dependencies import get_current_user
from app.models import ProjectOut, UserOut
from app.repositories import projects as projects_repo

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user=Depends(get_current_user)) -> UserOut:
    pool = get_pool()
    async with pool.acquire() as conn:
        project = await projects_repo.get_by_owner(conn, user["id"])

    return UserOut(
        id=user["id"],
        email=user["email"],
        created_at=user["created_at"],
        project=ProjectOut(**dict(project)) if project else None,
    )
