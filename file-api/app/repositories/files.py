from uuid import UUID

import asyncpg

type DBConnection = asyncpg.Connection | asyncpg.pool.PoolConnectionProxy


async def get_by_id_in_project(
    conn: DBConnection, file_id: UUID, project_id: UUID
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT f.*, t.status AS indexing_status
        FROM files f
        LEFT JOIN tasks t ON t.id = f.latest_task_id
        WHERE f.id = $1 AND f.project_id = $2
        """,
        file_id,
        project_id,
    )


async def list_by_folder(
    conn: DBConnection, project_id: UUID, folder_id: UUID | None
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT f.*, t.status AS indexing_status
        FROM files f
        LEFT JOIN tasks t ON t.id = f.latest_task_id
        WHERE f.project_id = $1 AND f.folder_id IS NOT DISTINCT FROM $2
        ORDER BY f.name
        """,
        project_id,
        folder_id,
    )


async def list_in_folders(
    conn: DBConnection, project_id: UUID, folder_ids: list[UUID]
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT id, name, storage_key FROM files
        WHERE project_id = $1 AND folder_id = ANY($2::uuid[])
        """,
        project_id,
        folder_ids,
    )


async def list_by_ids(
    conn: DBConnection, project_id: UUID, file_ids: list[UUID]
) -> list[asyncpg.Record]:
    if not file_ids:
        return []
    return await conn.fetch(
        "SELECT * FROM files WHERE project_id = $1 AND id = ANY($2::uuid[])",
        project_id,
        file_ids,
    )


async def set_latest_task(conn: DBConnection, file_id: UUID, task_id: UUID) -> None:
    await conn.execute(
        "UPDATE files SET latest_task_id = $1 WHERE id = $2", task_id, file_id
    )


async def delete(conn: DBConnection, file_id: UUID, project_id: UUID) -> None:
    await conn.execute(
        "DELETE FROM files WHERE id = $1 AND project_id = $2", file_id, project_id
    )


async def update_content(
    conn: DBConnection,
    file_id: UUID,
    project_id: UUID,
    *,
    content_type: str | None,
    size_bytes: int,
) -> asyncpg.Record:
    # name/folder_id are untouched - replacing a file's content keeps its
    # identity in the system, regardless of what the replacement upload
    # happens to be named locally.
    record = await conn.fetchrow(
        """
        UPDATE files
        SET content_type = $3, size_bytes = $4
        WHERE id = $1 AND project_id = $2
        RETURNING *
        """,
        file_id,
        project_id,
        content_type,
        size_bytes,
    )
    if not record:
        raise Exception("Unable to update file")
    return record


async def create(
    conn: DBConnection | asyncpg.pool.PoolConnectionProxy,
    *,
    file_id: UUID,
    project_id: UUID,
    folder_id: UUID | None,
    name: str,
    content_type: str | None,
    size_bytes: int,
    storage_key: str,
) -> asyncpg.Record:
    record = await conn.fetchrow(
        """
        INSERT INTO files (id, project_id, folder_id, name, content_type, size_bytes, storage_key)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """,
        file_id,
        project_id,
        folder_id,
        name,
        content_type,
        size_bytes,
        storage_key,
    )
    if not record:
        raise Exception("Unable to create file")
    return record
