import logging

from saq import Queue

from worker import db, milvus_client
from worker.config import settings as app_settings
from worker.tasks.delete_file import delete_file_vectors_batch
from worker.tasks.process_file import process_file

logger = logging.getLogger(__name__)

queue = Queue.from_url(app_settings.redis_url)


async def startup(ctx: dict) -> None:
    await milvus_client.connect()
    await db.connect()
    ctx["milvus"] = milvus_client.get_client()


async def shutdown(ctx: dict) -> None:
    await milvus_client.disconnect()
    await db.disconnect()


settings = {
    "queue": queue,
    "functions": [process_file, delete_file_vectors_batch],
    "concurrency": 10,
    "startup": startup,
    "shutdown": shutdown,
}
