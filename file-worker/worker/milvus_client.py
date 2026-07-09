from uuid import UUID

from pymilvus import AsyncMilvusClient, DataType

from worker.config import settings

# Shared with main.py's pre-upsert length check, so the schema and the
# validation guarding it can never drift apart.
TEXT_MAX_LENGTH = 8192

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
    # Milvus collection names must start with a letter/underscore and can't
    # contain hyphens - .hex drops the UUID's hyphens for us.
    return f"project_{project_id.hex}"


async def ensure_collection(project_id: UUID) -> str:
    """Creates the given project's chunk collection if it doesn't already
    exist. Safe to call before every processing run as it's idempotent"""
    milvus = get_client()
    name = collection_name_for_project(project_id)

    if await milvus.has_collection(name):
        print("milvus collection exists")
        return name

    print("milvus collection is being created")
    schema = milvus.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field(
        field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=128
    )
    # Partition key - root-level files (no real folder) use
    # settings.root_folder_partition_key as a sentinel instead of null.
    schema.add_field(
        field_name="folder_id",
        datatype=DataType.VARCHAR,
        is_partition_key=True,
        max_length=64,
    )
    schema.add_field(field_name="file_id", datatype=DataType.VARCHAR, max_length=64)
    schema.add_field(field_name="chunk_index", datatype=DataType.INT16)
    schema.add_field(
        field_name="text", datatype=DataType.VARCHAR, max_length=TEXT_MAX_LENGTH
    )
    schema.add_field(
        field_name="embedding",
        datatype=DataType.FLOAT_VECTOR,
        dim=settings.embedding_dimension,
    )

    index_params = milvus.prepare_index_params()
    index_params.add_index(
        field_name="embedding", index_type="AUTOINDEX", metric_type="COSINE"
    )

    await milvus.create_collection(
        collection_name=name, schema=schema, index_params=index_params
    )
    print("milvus collection created")
    return name
