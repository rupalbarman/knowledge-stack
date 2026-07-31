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
            f.folder_id,
            f.latest_task_id
        FROM tasks t
        JOIN files f ON f.id = t.file_ref
        WHERE t.id = $1
        """,
        task_id,
    )


async def get_by_ids(conn: DBConnection, task_ids: list[UUID]) -> list[asyncpg.Record]:
    # tasks would have reference to the file (even if it is deleted)
    return await conn.fetch(
        "SELECT * FROM tasks WHERE id = ANY($1::uuid[])", task_ids
    )


async def mark_processing(conn: DBConnection, task_id: UUID) -> None:
    await conn.execute(
        "UPDATE tasks SET status = 'processing', started_at = now() WHERE id = $1",
        task_id,
    )


async def mark_processing_batch(conn: DBConnection, task_ids: list[UUID]) -> None:
    await conn.execute(
        "UPDATE tasks SET status = 'processing', started_at = now() WHERE id = ANY($1::uuid[])",
        task_ids,
    )


async def mark_completed(
    conn: DBConnection, task_id: UUID, nb_chunks: int | None = None
) -> None:
    await conn.execute(
        "UPDATE tasks SET status = 'completed', completed_at = now(), nb_chunks = $2 WHERE id = $1",
        task_id,
        nb_chunks,
    )


async def mark_completed_batch(conn: DBConnection, task_ids: list[UUID]) -> None:
    await conn.execute(
        "UPDATE tasks SET status = 'completed', completed_at = now() WHERE id = ANY($1::uuid[])",
        task_ids,
    )


async def mark_failed(conn: DBConnection, task_id: UUID, error: str) -> None:
    await conn.execute(
        "UPDATE tasks SET status = 'failed', error = $2, completed_at = now() WHERE id = $1",
        task_id,
        error,
    )


async def mark_failed_batch(
    conn: DBConnection, task_ids: list[UUID], error: str
) -> None:
    await conn.execute(
        "UPDATE tasks SET status = 'failed', error = $2, completed_at = now() WHERE id = ANY($1::uuid[])",
        task_ids,
        error,
    )


async def mark_superseded(conn: DBConnection, task_id: UUID) -> None:
    await conn.execute(
        "UPDATE tasks SET status = 'superseded', completed_at = now() WHERE id = $1",
        task_id,
    )
