from uuid import UUID

import asyncpg

type DBConnection = asyncpg.Connection | asyncpg.pool.PoolConnectionProxy


async def create(
    conn: DBConnection, project_id: UUID, name: str, owner_id: UUID
) -> asyncpg.Record:
    record = await conn.fetchrow(
        "INSERT INTO projects (id, name, owner_id) VALUES ($1, $2, $3) RETURNING *",
        project_id,
        name,
        owner_id,
    )
    if not record:
        raise Exception("Unable to fetch record")
    return record


async def get_by_owner(conn: DBConnection, owner_id: str) -> asyncpg.Record | None:
    return await conn.fetchrow("SELECT * FROM projects WHERE owner_id = $1", owner_id)
