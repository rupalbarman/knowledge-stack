from uuid import UUID

import asyncpg

type DBConnection = asyncpg.Connection | asyncpg.pool.PoolConnectionProxy


async def get_with_file(conn: DBConnection, task_id: UUID) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT
            t.id AS task_id,
            t.status AS task_status,
            t.file_ref,
            t.project_id,
            f.name,
            f.storage_key,
            f.latest_task_id
        FROM tasks t
        JOIN files f ON f.id = t.file_ref
        WHERE t.id = $1
        """,
        task_id,
    )


async def get_by_id(conn: DBConnection, task_id: UUID) -> asyncpg.Record | None:
    # No join to files - file_ref/file_name on tasks are denormalized
    # snapshots that outlive the file itself, which is exactly what the
    # delete path needs (the file row is already gone by the time this runs).
    return await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)


async def mark_processing(conn: DBConnection, task_id: UUID) -> None:
    await conn.execute(
        "UPDATE tasks SET status = 'processing', started_at = now() WHERE id = $1",
        task_id,
    )


async def mark_completed(conn: DBConnection, task_id: UUID) -> None:
    await conn.execute(
        "UPDATE tasks SET status = 'completed', completed_at = now() WHERE id = $1",
        task_id,
    )


async def mark_failed(conn: DBConnection, task_id: UUID, error: str) -> None:
    await conn.execute(
        "UPDATE tasks SET status = 'failed', error = $2, completed_at = now() WHERE id = $1",
        task_id,
        error,
    )


async def mark_superseded(conn: DBConnection, task_id: UUID) -> None:
    await conn.execute(
        "UPDATE tasks SET status = 'superseded', completed_at = now() WHERE id = $1",
        task_id,
    )
