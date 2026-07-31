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


def _build_filters(
    project_id: UUID, file_id: UUID | None, status: TaskStatus | None
) -> tuple[str, list]:
    """Shared between list_by_project_id/count_by_project_id - both filter on
    the same optional (file_id, status) pair, only the rest of the query
    differs. Placeholder count varies with which filters are present, but
    every value is still a bound param - no string-built SQL values."""
    conditions = ["project_id = $1"]
    params: list = [project_id]

    if file_id is not None:
        params.append(file_id)
        conditions.append(f"file_ref = ${len(params)}")

    if status is not None:
        params.append(status)
        conditions.append(f"status = ${len(params)}")

    return " AND ".join(conditions), params


async def list_by_project_id(
    conn: DBConnection,
    project_id: UUID,
    file_id: UUID | None,
    status: TaskStatus | None,
    limit: int,
    offset: int,
) -> list[asyncpg.Record]:
    where_clause, params = _build_filters(project_id, file_id, status)
    params.extend([limit, offset])
    return await conn.fetch(
        f"""
        SELECT * FROM tasks
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """,
        *params,
    )


async def count_by_project_id(
    conn: DBConnection,
    project_id: UUID,
    file_id: UUID | None,
    status: TaskStatus | None,
) -> int:
    where_clause, params = _build_filters(project_id, file_id, status)
    return await conn.fetchval(
        f"SELECT COUNT(*) FROM tasks WHERE {where_clause}", *params
    ) or 0
