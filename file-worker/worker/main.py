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


async def delete_file_vectors_batch(ctx: dict, *, task_ids: list[str]) -> dict:
    task_uuids = [UUID(t) for t in task_ids]
    pool = db.get_pool()

    async with pool.acquire() as conn:
        tasks = await tasks_repo.get_by_ids(conn, task_uuids)
        if not tasks:
            logger.warning("delete batch %s: no matching tasks, skipping", task_ids)
            return {"task_ids": task_ids, "status": "missing"}

        await tasks_repo.mark_processing_batch(conn, task_uuids)

        # delete associated file vector code goes here
        logger.info("delete_file_vectors_batch: %d file(s)", len(tasks))

        await tasks_repo.mark_completed_batch(conn, task_uuids)

    return {"task_ids": task_ids, "status": "completed", "count": len(tasks)}


# Check if the configuration below needs reading from env
settings = {
    "queue": queue,
    "functions": [process_file, delete_file_vectors_batch],
    "concurrency": 10,
    "startup": startup,
    "shutdown": shutdown,
}
