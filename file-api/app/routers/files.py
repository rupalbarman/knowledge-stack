from uuid import UUID, uuid4

import asyncpg
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.config import settings
from app.db import get_pool
from app.dependencies import get_current_project
from app.models import FileOut, Page, PresignedUrlOut, TaskOut
from app.queue import queue
from app.repositories import files as files_repo
from app.repositories import folders as folders_repo
from app.repositories import tasks as tasks_repo
from app.storage import (
    FileTooLargeError,
    delete_object,
    generate_presigned_download_url,
    upload_bytes_stream,
)

router = APIRouter(prefix="/files", tags=["files"])

RECENT_FILES_LIMIT = 50


@router.get("", response_model=list[FileOut])
async def list_files(
    folder_id: UUID | None = None, project=Depends(get_current_project)
) -> list[FileOut]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await files_repo.list_by_folder(conn, project["id"], folder_id)
    return [FileOut(**dict(row)) for row in rows]


@router.get("/recent", response_model=Page[FileOut])
async def list_recent_files(
    limit: int = RECENT_FILES_LIMIT,
    offset: int = 0,
    project=Depends(get_current_project),
) -> Page[FileOut]:
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="offset must be >= 0",
        )

    if limit <= 0 or limit > RECENT_FILES_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"limit must be >= 0 and <= {RECENT_FILES_LIMIT}",
        )

    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await files_repo.list_recent(conn, project["id"], limit, offset)
        total = await files_repo.count_by_project_and_folder_id(conn, project["id"])
    return Page[FileOut](
        items=[FileOut(**dict(row)) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{file_id}", response_model=FileOut)
async def get_file(file_id: UUID, project=Depends(get_current_project)) -> FileOut:
    pool = get_pool()
    async with pool.acquire() as conn:
        file = await files_repo.get_by_id_in_project(conn, file_id, project["id"])
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="file not found"
        )
    return FileOut(**dict(file))


@router.get("/{file_id}/download-url", response_model=PresignedUrlOut)
async def get_file_download_url(
    file_id: UUID, project=Depends(get_current_project)
) -> PresignedUrlOut:
    pool = get_pool()
    async with pool.acquire() as conn:
        file = await files_repo.get_by_id_in_project(conn, file_id, project["id"])
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="file not found"
        )

    url, expires_in = await generate_presigned_download_url(file["storage_key"])
    return PresignedUrlOut(url=url, expires_in=expires_in)


@router.post("/{file_id}/sync", response_model=TaskOut)
async def sync_file(file_id: UUID, project=Depends(get_current_project)) -> TaskOut:
    pool = get_pool()
    async with pool.acquire() as conn:
        file = await files_repo.get_by_id_in_project(conn, file_id, project["id"])
        if file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="file not found"
            )

        async with conn.transaction():
            task_id = uuid4()
            task = await tasks_repo.create(
                conn,
                task_id,
                project["id"],
                file["id"],
                file["name"],
                task_type="upsert_vectors",
                reason="manual",
            )
            await files_repo.set_latest_task(conn, file["id"], task_id)

    await queue.enqueue(
        "process_file",
        task_id=str(task_id),
        timeout=settings.process_file_job_timeout_sec,
    )

    return TaskOut(**dict(task))


@router.put("/{file_id}/content", response_model=FileOut)
async def replace_file_content(
    file_id: UUID,
    file: UploadFile = File(...),
    project=Depends(get_current_project),
) -> FileOut:
    pool = get_pool()
    async with pool.acquire() as conn:
        existing = await files_repo.get_by_id_in_project(conn, file_id, project["id"])
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="file not found"
            )

        # replacing content still uses the same s3 key (project/file)
        # todo(Rupal): same as create_file/delete_file - storage is written
        # before the transaction below, so a rollback here would leave the
        # object updated but the files row still pointing at the old metadata
        try:
            size_bytes = await upload_bytes_stream(
                existing["storage_key"], file, file.content_type
            )
        except FileTooLargeError as e:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=str(e),
            )

        async with conn.transaction():
            record = await files_repo.update_content(
                conn,
                file_id,
                project["id"],
                content_type=file.content_type,
                size_bytes=size_bytes,
            )

            task_id = uuid4()
            await tasks_repo.create(
                conn,
                task_id,
                project["id"],
                file_id,
                record["name"],
                task_type="upsert_vectors",
                reason="replace",
            )
            await files_repo.set_latest_task(conn, file_id, task_id)

    # process_file already deletes old chunks before upserting new ones, so
    # re-running the same pipeline against the new bytes is all that's needed.
    await queue.enqueue(
        "process_file",
        task_id=str(task_id),
        timeout=settings.process_file_job_timeout_sec,
    )

    return FileOut(**dict(record), indexing_status="pending")


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: UUID, project=Depends(get_current_project)) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        file = await files_repo.get_by_id_in_project(conn, file_id, project["id"])
        if file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="file not found"
            )

        # todo(Rupal): Deletion of file in storage happens before the deletion in db / record
        # If the transaction below rolls back, the files row survives pointing at a storage_key
        # that's already gone - a dangling reference
        await delete_object(file["storage_key"])

        async with conn.transaction():
            task_id = uuid4()
            await tasks_repo.create(
                conn,
                task_id,
                project["id"],
                file_id,
                file["name"],
                task_type="delete_vectors",
                reason="delete",
            )
            await files_repo.delete(conn, file_id, project["id"])

    await queue.enqueue("delete_file_vectors_batch", task_ids=[str(task_id)])


@router.post("", response_model=FileOut, status_code=status.HTTP_201_CREATED)
async def create_file(
    file: UploadFile = File(...),
    folder_id: str | None = Form(None),
    project=Depends(get_current_project),
) -> FileOut:
    parsed_folder_id: UUID | None = None
    if folder_id:
        try:
            parsed_folder_id = UUID(folder_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="folder_id is not a valid UUID",
            )

    pool = get_pool()
    async with pool.acquire() as conn:
        if parsed_folder_id is not None:
            folder = await folders_repo.get_by_id_in_project(
                conn, parsed_folder_id, project["id"]
            )
            if folder is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="folder_id does not belong to your project",
                )

        file_id = uuid4()
        storage_key = f"{project['id']}/{file_id}"

        # todo(Rupal): Notice how s3 upload is done before the file creation
        # If the transaction below rolls back, the uploaded bytes are left in RustFS with no
        # files row ever pointing at them - an orphaned object

        try:
            size_bytes = await upload_bytes_stream(storage_key, file, file.content_type)
        except FileTooLargeError as e:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=str(e),
            )

        async with conn.transaction():
            try:
                record = await files_repo.create(
                    conn,
                    file_id=file_id,
                    project_id=project["id"],
                    folder_id=parsed_folder_id,
                    name=file.filename or f"File_{file_id}",
                    content_type=file.content_type,
                    size_bytes=size_bytes,
                    storage_key=storage_key,
                )
            except asyncpg.UniqueViolationError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="a file with this name already exists here",
                )

            task_id = uuid4()
            await tasks_repo.create(
                conn,
                task_id,
                project["id"],
                record["id"],
                record["name"],
                task_type="upsert_vectors",
                reason="upload",
            )
            await files_repo.set_latest_task(conn, record["id"], task_id)

    # todo(Rupal): Notice enqueue is outside the transaction, but any failure above will skip this call so we are good
    await queue.enqueue(
        "process_file",
        task_id=str(task_id),
        timeout=settings.process_file_job_timeout_sec,
    )

    # Newly inserted file will create a new task entity which defaults to "pending"
    # status. So we can guarantee the status here without having to query or join with associated task.
    return FileOut(**dict(record), indexing_status="pending")
