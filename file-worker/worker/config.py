from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    milvus_uri: str = "http://localhost:19530"

    database_url: str = (
        "postgresql://knowledge_stack:knowledge_stack@localhost:5432/knowledge_stack"
    )

    rustfs_url: str = "http://localhost:9000"
    rustfs_access_key: str = "minioadmin"
    rustfs_secret_key: str = "minioadmin"
    rustfs_bucket_name: str = "content-bucket"
    rustfs_region: str = "us-east-1"

    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunking_strategy: str = "markdown_text"

    embedding_dimension: int = 1024
    # partition key for milvus collection, used to separate folders.
    # __root__ refers to files under project (without folders)
    root_folder_partition_key: str = "__root__"

    embeddings_url: str = ""
    embeddings_api_key: str = ""
    embeddings_model: str = ""
    # controls how many texts are sent to the embeddings model to avoid it from
    # raising a 413. Does not control the length of text
    embeddings_batch_size: int = 32

    ocr_url: str = ""
    ocr_api_key: str = ""
    ocr_model: str = ""

    # controls how many rows / chunks are upserted to milvus in one go
    milvus_upsert_batch_size: int = 200

    # debug-only: writes every extracted document's text to disk
    save_extracted_text: bool = False
    save_extracted_chunks: bool = False

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
