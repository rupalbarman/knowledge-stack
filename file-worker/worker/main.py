import asyncio
import logging
from uuid import UUID

from saq import Queue

from worker import db, embeddings, milvus_client, storage
from worker.chunkers import UnknownStrategyError, get_chunker
from worker.config import settings as app_settings
from worker.extractors import ExtractionError, UnsupportedFileTypeError, get_extractor
from worker.milvus_client import TEXT_MAX_LENGTH
from worker.repositories import tasks as tasks_repo
from worker.utils import chunked, save_to_temp_dir

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
        text = await extractor(row["name"], contents)

        if app_settings.save_extracted_text:
            await asyncio.to_thread(save_to_temp_dir, row["file_ref"], text)

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

    try:
        chunker = get_chunker(app_settings.chunking_strategy)
        chunks = await chunker(text)
        if app_settings.save_extracted_chunks:
            await asyncio.to_thread(
                save_to_temp_dir,
                f"{row['file_ref']}-chunks",
                "\n---CHUNK-BOUNDARY---\n".join(chunks),
            )
        logger.info(
            "extracted %d chunk(s) from %s (file %s)",
            len(chunks),
            row["name"],
            row["file_ref"],
        )
    except UnknownStrategyError as exc:
        async with pool.acquire() as conn:
            await tasks_repo.mark_failed(conn, task_uuid, str(exc))
        return {"task_id": task_id, "status": "failed", "error": str(exc)}
    except Exception as exc:
        async with pool.acquire() as conn:
            await tasks_repo.mark_failed(conn, task_uuid, str(exc))
        raise

    # Milvus text field varchar length is measured in bytes and we check the size
    # based on character encoding. For instance, thai text is 3 bytes per char in UTF-8
    oversized = [
        i
        for i, chunk in enumerate(chunks)
        if len(chunk.encode("utf-8")) > TEXT_MAX_LENGTH
    ]
    if oversized:
        # Not retryable since a chunk that's too long will be too long on every retry
        error = (
            f"chunk(s) {oversized} exceed the {TEXT_MAX_LENGTH}-byte "
            "Milvus text field limit"
        )
        async with pool.acquire() as conn:
            await tasks_repo.mark_failed(conn, task_uuid, error)
        return {"task_id": task_id, "status": "failed", "error": error}

    try:
        # Ensure collection and schema exists to insert rows into
        collection_name = await milvus_client.ensure_collection(row["project_id"])

        # todo(Rupal): There's no hard-check to ensure that input to the embedding model is falling
        # under its input token limit and the model could silently swallow up the error and return a partial
        # vector.
        # Consider using a tokenizer check here of the same embedding model
        vectors = await embeddings.embed(chunks)

        folder_id = (
            str(row["folder_id"])
            if row["folder_id"] is not None
            else app_settings.root_folder_partition_key
        )
        file_id = str(row["file_ref"])

        milvus_rows = [
            {
                "id": f"{file_id}:{i}",
                "folder_id": folder_id,
                "file_id": file_id,
                "chunk_index": i,
                "text": chunk,
                "dense": vector,
            }
            for i, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]

        async with pool.acquire() as conn:
            # Re-check right before the actual write. If a newer constructive task exists then
            # write the newer one and ignore this task by marking it superseded.
            current = await tasks_repo.get_with_file(conn, task_uuid)
            if current is None or current["latest_task_id"] != task_uuid:
                await tasks_repo.mark_superseded(conn, task_uuid)
                return {"task_id": task_id, "status": "superseded"}

        # Clear any chunks from a previous run before writing the new ones -
        # upsert() alone would leave stale trailing chunks behind if this
        # run produced fewer chunks than the last one
        await milvus_client.delete_file_chunks(collection_name, file_id)

        for batch in chunked(milvus_rows, app_settings.milvus_upsert_batch_size):
            await ctx["milvus"].upsert(collection_name=collection_name, data=batch)
    except Exception as exc:
        async with pool.acquire() as conn:
            await tasks_repo.mark_failed(conn, task_uuid, str(exc))
        raise

    async with pool.acquire() as conn:
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

        for task in tasks:
            collection_name = milvus_client.collection_name_for_project(
                task["project_id"]
            )
            await milvus_client.delete_file_chunks(
                collection_name, str(task["file_ref"])
            )

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
