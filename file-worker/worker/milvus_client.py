from pymilvus import AsyncMilvusClient

from worker.config import settings

client: AsyncMilvusClient | None = None


async def connect() -> None:
    global client
    client = AsyncMilvusClient(uri=settings.milvus_uri)


async def disconnect() -> None:
    if client is not None:
        await client.close()


def get_client() -> AsyncMilvusClient:
    assert client is not None, "milvus client not initialized"
    return client
