import asyncio
import logging
from uuid import UUID

from worker import db, milvus_client
from worker.repositories import tasks as tasks_repo

logger = logging.getLogger(__name__)


async def _fail_batch(
    conn: tasks_repo.DBConnection, task_uuids: list[UUID], exc: BaseException
) -> None:
    message = (
        "job cancelled or timed out"
        if isinstance(exc, asyncio.CancelledError)
        else str(exc)
    )
    await tasks_repo.mark_failed_batch(conn, task_uuids, message)


async def delete_file_vectors_batch(ctx: dict, *, task_ids: list[str]) -> dict:
    task_uuids = [UUID(t) for t in task_ids]
    pool = db.get_pool()

    async with pool.acquire() as conn:
        tasks = await tasks_repo.get_by_ids(conn, task_uuids)
        if not tasks:
            logger.warning("delete batch %s: no matching tasks, skipping", task_ids)
            return {"task_ids": task_ids, "status": "missing"}

        await tasks_repo.mark_processing_batch(conn, task_uuids)

        try:
            for task in tasks:
                collection_name = milvus_client.collection_name_for_project(
                    task["project_id"]
                )
                await milvus_client.delete_file_chunks(
                    collection_name, str(task["file_ref"])
                )

            logger.info("delete_file_vectors_batch: %d file(s)", len(tasks))

            await tasks_repo.mark_completed_batch(conn, task_uuids)
        except (Exception, asyncio.CancelledError) as exc:
            await _fail_batch(conn, task_uuids, exc)
            raise

    return {"task_ids": task_ids, "status": "completed", "count": len(tasks)}
