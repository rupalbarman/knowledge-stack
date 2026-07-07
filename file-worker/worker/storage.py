from contextlib import asynccontextmanager

import aioboto3

from worker.config import settings

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


async def download_bytes(key: str) -> bytes:
    async with s3_client() as client:
        response = await client.get_object(Bucket=settings.rustfs_bucket_name, Key=key)
        async with response["Body"] as stream:
            return await stream.read()
