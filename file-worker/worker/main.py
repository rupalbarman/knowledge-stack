from saq import Queue

from worker import milvus_client
from worker.config import settings as app_settings

queue = Queue.from_url(app_settings.redis_url)


async def startup(ctx: dict) -> None:
    await milvus_client.connect()
    ctx["milvus"] = milvus_client.get_client()


async def shutdown(ctx: dict) -> None:
    await milvus_client.disconnect()


async def process_file(
    ctx: dict, *, file_id: str, project_id: str, storage_key: str, name: str
) -> dict:
    # TODO: fetch bytes from RustFS via storage_key, chunk, embed, and upsert
    # into Milvus via ctx["milvus"]. For now this just confirms the message
    # made it from file-api through the queue to a worker.
    print(f"received file {file_id} ({name}) for project {project_id} at {storage_key}")
    return {"file_id": file_id, "status": "received"}


# Referenced by the Dockerfile CMD as `worker.main.settings` - saq's CLI
# looks up this exact name to configure the worker process.
settings = {
    "queue": queue,
    "functions": [process_file],
    "concurrency": 10,
    "startup": startup,
    "shutdown": shutdown,
}
