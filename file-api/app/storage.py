from contextlib import asynccontextmanager
from typing import Protocol

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings

# force path-style addressing (http://host/bucket/key) for S3. Refer official documentation
_S3_CONFIG = Config(signature_version="s3v4", s3={"addressing_style": "path"})


class FileTooLargeError(Exception):
    """Raised mid-upload once the stream exceeds settings.max_file_upload_bytes -
    checked as chunks arrive rather than after the full upload completes"""


class AsyncReadable(Protocol):
    async def read(self, size: int) -> bytes: ...


_session = aioboto3.Session()


@asynccontextmanager
async def s3_client():
    async with _session.client(
        "s3",
        endpoint_url=settings.rustfs_url,
        aws_access_key_id=settings.rustfs_access_key,
        aws_secret_access_key=settings.rustfs_secret_key,
        region_name=settings.rustfs_region,
        config=_S3_CONFIG,
    ) as client:
        yield client


@asynccontextmanager
async def s3_public_client():
    # Only ever used for signing presigned URLs, never to actually connect
    # Refer "storage_download_url"
    async with _session.client(
        "s3",
        endpoint_url=settings.storage_public_url,
        aws_access_key_id=settings.rustfs_access_key,
        aws_secret_access_key=settings.rustfs_secret_key,
        region_name=settings.rustfs_region,
        config=_S3_CONFIG,
    ) as client:
        yield client


async def ensure_bucket() -> None:
    async with s3_client() as client:
        try:
            await client.head_bucket(Bucket=settings.rustfs_bucket_name)
        except ClientError:
            await client.create_bucket(Bucket=settings.rustfs_bucket_name)


# unused for now
async def upload_bytes(key: str, data: bytes, content_type: str | None) -> None:
    if len(data) > settings.max_file_upload_bytes:
        raise FileTooLargeError(
            f"upload exceeded {settings.max_file_upload_bytes} bytes"
        )

    async with s3_client() as client:
        await client.put_object(
            Bucket=settings.rustfs_bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type or "application/octet-stream",
        )


async def upload_bytes_stream(
    key: str, file: AsyncReadable, content_type: str | None
) -> int:
    """Uploads `file` via S3 multipart upload, reading it in fixed-size
    chunks rather than buffering the whole thing into memory at once like
    upload_bytes() does. Returns the total number of bytes uploaded."""
    async with s3_client() as client:
        multipart = await client.create_multipart_upload(
            Bucket=settings.rustfs_bucket_name,
            Key=key,
            ContentType=content_type or "application/octet-stream",
        )
        upload_id = multipart["UploadId"]

        parts = []
        total_bytes = 0
        part_number = 1

        try:
            while True:
                chunk = await file.read(settings.upload_chunk_size)
                if not chunk:
                    break

                response = await client.upload_part(
                    Bucket=settings.rustfs_bucket_name,
                    Key=key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=chunk,
                )
                parts.append({"ETag": response["ETag"], "PartNumber": part_number})
                total_bytes += len(chunk)
                part_number += 1

                if total_bytes > settings.max_file_upload_bytes:
                    raise FileTooLargeError(
                        f"upload exceeded {settings.max_file_upload_bytes} bytes"
                    )
        except Exception:
            await client.abort_multipart_upload(
                Bucket=settings.rustfs_bucket_name, Key=key, UploadId=upload_id
            )
            raise

        if not parts:
            # Multipart upload requires at least one part - an empty file
            # has nothing to send, so fall back to a plain PUT instead.
            await client.abort_multipart_upload(
                Bucket=settings.rustfs_bucket_name, Key=key, UploadId=upload_id
            )
            await client.put_object(
                Bucket=settings.rustfs_bucket_name,
                Key=key,
                Body=b"",
                ContentType=content_type or "application/octet-stream",
            )
            return 0

        await client.complete_multipart_upload(
            Bucket=settings.rustfs_bucket_name,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
        return total_bytes


async def delete_object(key: str) -> None:
    async with s3_client() as client:
        # S3-compatible delete is idempotent - deleting a missing key is not an error.
        await client.delete_object(Bucket=settings.rustfs_bucket_name, Key=key)


async def generate_presigned_download_url(key: str) -> tuple[str, int]:
    expires_in = settings.download_url_expiry_hours * 3600
    async with s3_public_client() as client:
        url = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.rustfs_bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )
    return url, expires_in
