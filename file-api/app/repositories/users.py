from uuid import UUID

import asyncpg

type DBConnection = asyncpg.Connection | asyncpg.pool.PoolConnectionProxy


async def get_by_email(conn: DBConnection, email: str) -> asyncpg.Record | None:
    return await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)


async def get_by_id(conn: asyncpg.Connection, user_id: str) -> asyncpg.Record | None:
    return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)


async def create(
    conn: DBConnection, user_id: UUID, email: str, hashed_password: str
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3) RETURNING *",
        user_id,
        email,
        hashed_password,
    )
