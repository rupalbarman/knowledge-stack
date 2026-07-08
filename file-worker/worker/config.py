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

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
