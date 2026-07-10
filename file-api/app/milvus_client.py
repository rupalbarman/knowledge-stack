from uuid import UUID

from pymilvus import AsyncMilvusClient

from app.config import settings

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


def collection_name_for_project(project_id: UUID) -> str:
    # refer variant on file-worker. Both should match
    return f"project_{project_id.hex}"
