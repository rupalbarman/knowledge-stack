from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.db import get_pool
from app.dependencies import get_current_project
from app.milvus_client import collection_name_for_project, get_client
from app.models import SearchOptions, SearchRequest, SearchResponse
from app.pipeline import RAGPipeline
from app.repositories import folders as folders_repo

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(
    payload: SearchRequest, project=Depends(get_current_project)
) -> SearchResponse:
    options = payload.options or SearchOptions()
    top_k = options.top_k or settings.search_default_top_k

    if top_k <= 0 or top_k > settings.search_max_top_k:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"top_k must be between 1 and {settings.search_max_top_k}",
        )

    pool = get_pool()

    if payload.folder_id is not None:
        async with pool.acquire() as conn:
            folder = await folders_repo.get_by_id_in_project(
                conn, payload.folder_id, project["id"]
            )
        if folder is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="folder_id does not belong to your project",
            )

    milvus = get_client()
    collection_name = collection_name_for_project(project["id"])

    if not await milvus.has_collection(collection_name):
        return SearchResponse(hits=[])

    folder_id = (
        str(payload.folder_id)
        if payload.folder_id is not None
        else settings.root_folder_partition_key
    )

    filter_expr = f'folder_id == "{folder_id}"'

    pipeline = RAGPipeline(pool=pool, milvus=milvus)
    hits = await pipeline.retrieve(
        request=payload, project_id=project["id"], filter_expr=filter_expr
    )

    return SearchResponse(hits=hits)
