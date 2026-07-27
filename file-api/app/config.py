from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    database_url: str = (
        "postgresql://knowledge_stack:knowledge_stack@localhost:5432/knowledge_stack"
    )
    redis_url: str = "redis://localhost:6379"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 120

    rustfs_url: str = "http://localhost:9000"
    rustfs_access_key: str = "minioadmin"
    rustfs_secret_key: str = "minioadmin"
    rustfs_bucket_name: str = "content-bucket"
    rustfs_region: str = "us-east-1"

    # Used only to sign presigned URLs for downloads
    storage_public_url: str = "http://localhost:9000"
    download_url_expiry_hours: int = 1

    # Max number of file vectors to be deleted
    delete_batch_size: int = 100
    # Timeout for process_file job
    process_file_job_timeout_sec: int = 600

    # Size of each part in a multipart upload to RustFS / S3 (8 MB)
    upload_chunk_size_bytes: int = 8 * 1024 * 1024
    # Hard cap on a single file upload size (20 MB)
    max_file_upload_bytes: int = 20 * 1024 * 1024

    milvus_uri: str = "http://localhost:19530"

    embeddings_url: str = ""
    embeddings_api_key: str = ""
    embeddings_model: str = ""

    reranker_enabled: bool = True
    reranker_model: str = ""
    reranker_url: str = ""
    reranker_api_key: str = ""

    # Must match file-worker's setting
    root_folder_partition_key: str = "__root__"

    search_default_top_k: int = 10
    search_max_top_k: int = 50

    # Comma-separated list of origins allowed to call this API from a browser (the ui/ app)
    cors_allowed_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
