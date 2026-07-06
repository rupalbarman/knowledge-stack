from contextlib import asynccontextmanager

import aioboto3
from botocore.exceptions import ClientError

from app.config import settings

_session = aioboto3.Session()


@asynccontextmanager
async def s3_client():
    async with _session.client(
        "s3",
        endpoint_url=settings.rustfs_url,
        aws_access_key_id=settings.rustfs_access_key,
        aws_secret_access_key=settings.rustfs_secret_key,
    ) as client:
        yield client


async def ensure_bucket() -> None:
    async with s3_client() as client:
        try:
            await client.head_bucket(Bucket=settings.rustfs_bucket_name)
        except ClientError:
            await client.create_bucket(Bucket=settings.rustfs_bucket_name)


async def upload_bytes(key: str, data: bytes, content_type: str | None) -> None:
    async with s3_client() as client:
        await client.put_object(
            Bucket=settings.rustfs_bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type or "application/octet-stream",
        )


async def delete_object(key: str) -> None:
    async with s3_client() as client:
        # S3-compatible delete is idempotent - deleting a missing key is not an error.
        await client.delete_object(Bucket=settings.rustfs_bucket_name, Key=key)
