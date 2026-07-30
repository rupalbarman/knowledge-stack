from uuid import UUID

import asyncpg

type DBConnection = asyncpg.Connection | asyncpg.pool.PoolConnectionProxy


async def get_summary(conn: DBConnection, project_id: UUID) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        SELECT
            COUNT(f.id) AS total_documents,
            COALESCE(SUM(f.size_bytes), 0) AS storage_used_bytes,
            COALESCE(SUM(t.nb_chunks), 0) AS total_chunks,
            COUNT(*) FILTER (WHERE t.status = 'pending') AS pending_documents,
            COUNT(*) FILTER (WHERE t.status = 'processing') AS processing_documents,
            COUNT(*) FILTER (WHERE t.status = 'completed') AS completed_documents,
            COUNT(*) FILTER (WHERE t.status = 'failed') AS failed_documents
        FROM files f
        LEFT JOIN tasks t ON t.id = f.latest_task_id
        WHERE f.project_id = $1
        """,
        project_id,
    )
