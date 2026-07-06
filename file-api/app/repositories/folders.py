from uuid import UUID

import asyncpg

type DBConnection = asyncpg.Connection | asyncpg.pool.PoolConnectionProxy


async def get_by_id_in_project(
    conn: DBConnection, folder_id: UUID, project_id: UUID
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        "SELECT * FROM folders WHERE id = $1 AND project_id = $2",
        folder_id,
        project_id,
    )


async def list_by_parent(
    conn: DBConnection, project_id: UUID, parent_id: UUID | None
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT * FROM folders
        WHERE project_id = $1 AND parent_id IS NOT DISTINCT FROM $2
        ORDER BY name
        """,
        project_id,
        parent_id,
    )


async def list_descendant_ids(
    conn: DBConnection, folder_id: UUID, project_id: UUID
) -> list[UUID]:
    rows = await conn.fetch(
        """
        WITH RECURSIVE descendants AS (
            SELECT id FROM folders WHERE id = $1 AND project_id = $2
            UNION ALL
            SELECT f.id FROM folders f
            JOIN descendants d ON f.parent_id = d.id
        )
        SELECT id FROM descendants
        """,
        folder_id,
        project_id,
    )
    return [r["id"] for r in rows]


async def delete(conn: DBConnection, folder_id: UUID, project_id: UUID) -> None:
    # Cascades to sub-folders and their files' metadata via FK ON DELETE CASCADE.
    # Callers must delete the underlying storage objects first (see routers/folders.py).
    await conn.execute(
        "DELETE FROM folders WHERE id = $1 AND project_id = $2", folder_id, project_id
    )


async def create(
    conn: DBConnection,
    folder_id: UUID,
    project_id: UUID,
    parent_id: UUID | None,
    name: str,
) -> asyncpg.Record:
    record = await conn.fetchrow(
        """
        INSERT INTO folders (id, project_id, parent_id, name)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        folder_id,
        project_id,
        parent_id,
        name,
    )
    if not record:
        raise Exception("Unable to create folder")
    return record
