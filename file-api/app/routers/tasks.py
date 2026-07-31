from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_pool
from app.dependencies import get_current_project
from app.models import Page, TaskOut
from app.repositories import tasks as tasks_repo

router = APIRouter(prefix="/tasks", tags=["tasks"])

LIMIT = 100


@router.get("", response_model=Page[TaskOut])
async def list_tasks(
    file_id: UUID | None = None,
    limit: int = LIMIT,
    offset: int = 0,
    project=Depends(get_current_project),
) -> Page[TaskOut]:
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="offset must be >= 0",
        )

    if limit <= 0 or limit > LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"limit must be >= 0 and <= {LIMIT}",
        )

    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await tasks_repo.list_by_project_id(
            conn,
            project["id"],
            file_id,
            limit,
            offset,
        )
        total = await tasks_repo.count_by_project_id(conn, project["id"], file_id)

    return Page[TaskOut](
        items=[TaskOut(**dict(row)) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
