from fastapi import APIRouter, Depends

from app.db import get_pool
from app.dependencies import get_current_project
from app.models import TaskOut
from app.repositories import tasks as tasks_repo

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
async def list_tasks(project=Depends(get_current_project)) -> list[TaskOut]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await tasks_repo.list_by_project_id(conn, project["id"])

    return [TaskOut(**dict(row)) for row in rows]
