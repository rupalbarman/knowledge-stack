import asyncio
import logging
from uuid import UUID

from saq import Queue

from worker import chunking, db, milvus_client, storage
from worker.config import settings as app_settings
from worker.extractors import ExtractionError, UnsupportedFileTypeError, get_extractor
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

    try:
        extractor = get_extractor(row["name"])
        text = await asyncio.to_thread(extractor, contents)
        print(text)
    except (UnsupportedFileTypeError, ExtractionError) as exc:
        # Not retryable - the file's type/content won't change on its own,
        # so there's no point letting saq retry this job.
        async with pool.acquire() as conn:
            await tasks_repo.mark_failed(conn, task_uuid, str(exc))
        return {"task_id": task_id, "status": "failed", "error": str(exc)}
    except Exception as exc:
        async with pool.acquire() as conn:
            await tasks_repo.mark_failed(conn, task_uuid, str(exc))
        raise

    chunks = await asyncio.to_thread(chunking.chunk_text, text)

    # TODO: embed chunks and upsert into Milvus via ctx["milvus"].
    logger.info(
        "extracted %d chunk(s) from %s (file %s)",
        len(chunks),
        row["name"],
        row["file_ref"],
    )

    async with pool.acquire() as conn:
        # Re-check right before the "commit" point: a newer task may have
        # been created while this one was mid-flight.
        current = await tasks_repo.get_with_file(conn, task_uuid)
        if current is None or current["latest_task_id"] != task_uuid:
            await tasks_repo.mark_superseded(conn, task_uuid)
            return {"task_id": task_id, "status": "superseded"}

        # Placeholder completion until the embed/upsert steps exist - marks
        # that extraction and chunking succeeded end to end.
        await tasks_repo.mark_completed(conn, task_uuid)

    return {"task_id": task_id, "status": "completed", "chunks": len(chunks)}


async def delete_file_vectors(ctx: dict, *, task_id: str) -> dict:
    task_uuid = UUID(task_id)
    pool = db.get_pool()

    async with pool.acquire() as conn:
        task = await tasks_repo.get_by_id(conn, task_uuid)
        if task is None:
            logger.warning("delete task %s not found, skipping", task_id)
            return {"task_id": task_id, "status": "missing"}

        await tasks_repo.mark_processing(conn, task_uuid)

    # The files row is already gone by the time this runs (file-api enqueues
    # after deleting it) - file_ref/file_name/project_id come straight off
    # the task's own denormalized snapshot, no join needed.
    # TODO: delete matching rows from Milvus via ctx["milvus"] once the
    # embed/upsert side exists, e.g.
    #   await ctx["milvus"].delete(
    #       collection_name=..., filter=f'file_id == "{task["file_ref"]}"'
    #   )
    logger.info(
        "delete_file_vectors: file %s (%s) for project %s",
        task["file_ref"],
        task["file_name"],
        task["project_id"],
    )

    async with pool.acquire() as conn:
        await tasks_repo.mark_completed(conn, task_uuid)

    return {"task_id": task_id, "status": "completed"}


# Referenced by the Dockerfile CMD as `worker.main.settings` - saq's CLI
# looks up this exact name to configure the worker process.
settings = {
    "queue": queue,
    "functions": [process_file, delete_file_vectors],
    "concurrency": 10,
    "startup": startup,
    "shutdown": shutdown,
}
