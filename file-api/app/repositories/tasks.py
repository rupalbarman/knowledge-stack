from typing import Literal
from uuid import UUID

import asyncpg

type DBConnection = asyncpg.Connection | asyncpg.pool.PoolConnectionProxy

TaskType = Literal["upsert_vectors", "delete_vectors"]
TaskReason = Literal["upload", "manual", "delete", "replace"]
TaskStatus = Literal["pending", "processing", "completed", "failed", "superseded"]


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


async def create_batch(
    conn: DBConnection,
    project_id: UUID,
    task_ids_and_files: list[tuple[UUID, UUID, str]],
    task_type: TaskType,
    reason: TaskReason,
) -> list[asyncpg.Record]:
    """Bulk-insert one task per (task_id, file_ref, file_name) tuple in a
    single round trip, instead of one INSERT per file."""
    if not task_ids_and_files:
        return []

    task_ids, file_refs, file_names = zip(*task_ids_and_files)
    return await conn.fetch(
        """
        INSERT INTO tasks (id, project_id, file_ref, file_name, type, reason)
        SELECT t.id, $1, t.file_ref, t.file_name, $2, $3
        FROM unnest($4::uuid[], $5::uuid[], $6::text[]) AS t(id, file_ref, file_name)
        RETURNING *
        """,
        project_id,
        task_type,
        reason,
        list(task_ids),
        list(file_refs),
        list(file_names),
    )


async def list_by_project_id(
    conn: DBConnection,
    project_id: UUID,
    file_id: UUID | None,
    limit: int,
    offset: int,
) -> list[asyncpg.Record]:
    if file_id is not None:
        return await conn.fetch(
            """
            SELECT * FROM tasks
            WHERE project_id = $1 AND file_ref = $2
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
            """,
            project_id,
            file_id,
            limit,
            offset,
        )

    return await conn.fetch(
        """
        SELECT * FROM tasks
        WHERE project_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """,
        project_id,
        limit,
        offset,
    )


async def count_by_project_id(
    conn: DBConnection, project_id: UUID, file_id: UUID | None
) -> int:
    if file_id is not None:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM tasks WHERE project_id = $1 AND file_ref = $2",
            project_id,
            file_id,
        )

    return await conn.fetchval(
        "SELECT COUNT(*) FROM tasks WHERE project_id = $1", project_id
    )
