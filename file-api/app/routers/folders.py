from uuid import UUID, uuid4

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_pool
from app.dependencies import get_current_project
from app.models import FolderCreateRequest, FolderOut
from app.repositories import files as files_repo
from app.repositories import folders as folders_repo
from app.storage import delete_object

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("", response_model=list[FolderOut])
async def list_folders(
    parent_id: UUID | None = None, project=Depends(get_current_project)
) -> list[FolderOut]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await folders_repo.list_by_parent(conn, project["id"], parent_id)
    return [FolderOut(**dict(row)) for row in rows]


@router.get("/{folder_id}", response_model=FolderOut)
async def get_folder(
    folder_id: UUID, project=Depends(get_current_project)
) -> FolderOut:
    pool = get_pool()
    async with pool.acquire() as conn:
        folder = await folders_repo.get_by_id_in_project(
            conn, folder_id, project["id"]
        )
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="folder not found"
        )
    return FolderOut(**dict(folder))


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(folder_id: UUID, project=Depends(get_current_project)) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        folder = await folders_repo.get_by_id_in_project(
            conn, folder_id, project["id"]
        )
        if folder is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="folder not found"
            )

        # Include the folder itself plus every nested sub-folder, since deleting it
        # cascades through all of them in Postgres - the storage objects for every
        # file at any depth need to be cleaned up before that cascade fires.
        descendant_ids = await folders_repo.list_descendant_ids(
            conn, folder_id, project["id"]
        )
        storage_keys = await files_repo.list_storage_keys_in_folders(
            conn, project["id"], descendant_ids
        )
        for key in storage_keys:
            await delete_object(key)

        await folders_repo.delete(conn, folder_id, project["id"])


@router.post("", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
async def create_folder(
    payload: FolderCreateRequest, project=Depends(get_current_project)
) -> FolderOut:
    pool = get_pool()
    async with pool.acquire() as conn:
        if payload.parent_id is not None:
            parent = await folders_repo.get_by_id_in_project(
                conn, payload.parent_id, project["id"]
            )
            if parent is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="parent_id does not belong to your project",
                )

        try:
            folder = await folders_repo.create(
                conn, uuid4(), project["id"], payload.parent_id, payload.name
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="a folder with this name already exists here",
            )

    return FolderOut(**dict(folder))
