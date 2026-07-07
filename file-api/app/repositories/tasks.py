from uuid import UUID

import asyncpg

type DbConnection = asyncpg.Connection | asyncpg.pool.PoolConnectionProxy


async def create(
    conn: DbConnection, task_id: UUID, project_id: UUID, file_id: UUID
) -> asyncpg.Record:
    record = await conn.fetchrow(
        """
        INSERT INTO tasks (id, project_id, file_id)
        VALUES ($1, $2, $3)
        RETURNING *
        """,
        task_id,
        project_id,
        file_id,
    )
    if not record:
        raise Exception("Unable to create task")
    return record


async def list_by_project_id(
    conn: DbConnection, project_id: UUID
) -> list[asyncpg.Record]:
    records = await conn.fetch(
        "SELECT * FROM tasks WHERE project_id = $1 ORDER BY created_at DESC",
        project_id,
    )
    return records
