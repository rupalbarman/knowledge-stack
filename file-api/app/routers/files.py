from uuid import UUID, uuid4

import asyncpg
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.db import get_pool
from app.dependencies import get_current_project
from app.models import FileOut
from app.queue import queue
from app.repositories import files as files_repo
from app.repositories import folders as folders_repo
from app.repositories import tasks as tasks_repo
from app.storage import delete_object, upload_bytes

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=list[FileOut])
async def list_files(
    folder_id: UUID | None = None, project=Depends(get_current_project)
) -> list[FileOut]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await files_repo.list_by_folder(conn, project["id"], folder_id)
    return [FileOut(**dict(row)) for row in rows]


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


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: UUID, project=Depends(get_current_project)) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        file = await files_repo.get_by_id_in_project(conn, file_id, project["id"])
        if file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="file not found"
            )

        await delete_object(file["storage_key"])
        await files_repo.delete(conn, file_id, project["id"])


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

        contents = await file.read()
        file_id = uuid4()
        storage_key = f"{project['id']}/{file_id}"

        # todo(Rupal): Notice how s3 upload is done before the file creation - possible orphaned object, handle it
        await upload_bytes(storage_key, contents, file.content_type)

        async with conn.transaction():
            try:
                record = await files_repo.create(
                    conn,
                    file_id=file_id,
                    project_id=project["id"],
                    folder_id=parsed_folder_id,
                    name=file.filename or f"File_{file_id}",
                    content_type=file.content_type,
                    size_bytes=len(contents),
                    storage_key=storage_key,
                )
            except asyncpg.UniqueViolationError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="a file with this name already exists here",
                )

            task_id = uuid4()
            await tasks_repo.create(conn, task_id, project["id"], record["id"])
            await files_repo.set_latest_task(conn, record["id"], task_id)

    # todo(Rupal): Notice enqueue is outside the transaction, but any failure above will skip this call so we are good
    await queue.enqueue("process_file", task_id=str(task_id))

    return FileOut(**dict(record))
