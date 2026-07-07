import logging
from uuid import UUID

from saq import Queue

from worker import db, milvus_client, storage
from worker.config import settings as app_settings
from worker.repositories import tasks as tasks_repo

logger = logging.getLogger(__name__)

queue = Queue.from_url(app_settings.redis_url)


async def startup(ctx: dict) -> None:
    await milvus_client.connect()
    await db.connect()
    ctx["milvus"] = milvus_client.get_client()


async def shutdown(ctx: dict) -> None:
    await milvus_client.disconnect()
    await db.disconnect()


async def process_file(ctx: dict, *, task_id: str) -> dict:
    task_uuid = UUID(task_id)
    pool = db.get_pool()
    logger.info("process_file: %s", task_id)

    async with pool.acquire() as conn:
        row = await tasks_repo.get_with_file(conn, task_uuid)
        if row is None:
            logger.warning("task %s has no matching row, skipping", task_id)
            return {"task_id": task_id, "status": "missing"}

        if row["latest_task_id"] != task_uuid:
            await tasks_repo.mark_superseded(conn, task_uuid)
            return {"task_id": task_id, "status": "superseded"}

        await tasks_repo.mark_processing(conn, task_uuid)

    try:
        contents = await storage.download_bytes(row["storage_key"])
    except Exception as exc:
        async with pool.acquire() as conn:
            await tasks_repo.mark_failed(conn, task_uuid, str(exc))
        raise

    # TODO: extract text, chunk, embed, and upsert into Milvus via ctx["milvus"].
    # This still just confirms the file's current bytes are reachable end to
    # end - extraction/chunking/embedding land once those are decided.
    logger.info(
        "downloaded %s (%d bytes) for file %s",
        row["storage_key"],
        len(contents),
        row["file_id"],
    )

    async with pool.acquire() as conn:
        # Re-check right before the "commit" point: a newer task may have
        # been created while this one was mid-flight.
        current = await tasks_repo.get_with_file(conn, task_uuid)
        if current is None or current["latest_task_id"] != task_uuid:
            await tasks_repo.mark_superseded(conn, task_uuid)
            return {"task_id": task_id, "status": "superseded"}

        # Placeholder completion until the real extract/chunk/embed/upsert
        # pipeline exists - marks that the base plumbing succeeded end to end.
        await tasks_repo.mark_completed(conn, task_uuid)

    return {"task_id": task_id, "status": "completed"}


# Referenced by the Dockerfile CMD as `worker.main.settings` - saq's CLI
# looks up this exact name to configure the worker process.
settings = {
    "queue": queue,
    "functions": [process_file],
    "concurrency": 10,
    "startup": startup,
    "shutdown": shutdown,
}
