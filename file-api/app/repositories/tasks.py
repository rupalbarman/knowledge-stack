from typing import Literal
from uuid import UUID

import asyncpg

type DBConnection = asyncpg.Connection | asyncpg.pool.PoolConnectionProxy

TaskType = Literal["vectorize", "delete_vectors"]
TaskReason = Literal["upload", "manual", "delete"]


async def create(
    conn: DBConnection,
    task_id: UUID,
    project_id: UUID,
    file_ref: UUID,
    file_name: str,
    task_type: TaskType,
    reason: TaskReason,
) -> asyncpg.Record:
    record = await conn.fetchrow(
        """
        INSERT INTO tasks (id, project_id, file_ref, file_name, type, reason)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        task_id,
        project_id,
        file_ref,
        file_name,
        task_type,
        reason,
    )
    if not record:
        raise Exception("Unable to create task")
    return record


async def list_by_project_id(
    conn: DBConnection, project_id: UUID
) -> list[asyncpg.Record]:
    records = await conn.fetch(
        "SELECT * FROM tasks WHERE project_id = $1 ORDER BY created_at DESC",
        project_id,
    )
    return records
