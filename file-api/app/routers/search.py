from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.db import get_pool
from app.dependencies import get_current_project
from app.embeddings import embed
from app.milvus_client import collection_name_for_project, get_client
from app.models import SearchHit, SearchOptions, SearchRequest, SearchResponse
from app.repositories import files as files_repo
from app.repositories import folders as folders_repo

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(
    payload: SearchRequest, project=Depends(get_current_project)
) -> SearchResponse:
    options = payload.options or SearchOptions()
    top_k = options.top_k or settings.search_default_top_k
    min_score = options.min_score

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

    if options.mode == "dense":
        vectors = await embed([payload.query])
        query_data = [vectors[0]]
    else:
        query_data = [payload.query]

    results = await milvus.search(
        collection_name=collection_name,
        data=query_data,
        anns_field=options.mode,
        filter=f'folder_id == "{folder_id}"',
        limit=top_k,
        output_fields=["file_id", "chunk_index", "text"],
    )
    raw_hits = results[0] if results else []

    if min_score is not None:
        # Higher the better. COSINE searches span from -1 to 1
        # while sparse searches are positive unbounded above 0
        raw_hits = [hit for hit in raw_hits if hit["distance"] >= min_score]

    if not raw_hits:
        return SearchResponse(hits=[])

    file_ids = list({UUID(hit["entity"]["file_id"]) for hit in raw_hits})
    async with pool.acquire() as conn:
        files = await files_repo.list_by_ids(conn, project["id"], file_ids)
    names_by_id = {f["id"]: f["name"] for f in files}

    hits = []
    for hit in raw_hits:
        file_id = UUID(hit["entity"]["file_id"])
        hits.append(
            SearchHit(
                file_id=file_id,
                # A hit can outlive its file if the delete-vectors cleanup
                # hasn't caught up yet - fall back rather than error.
                file_name=names_by_id.get(file_id, "(deleted file)"),
                chunk_index=hit["entity"]["chunk_index"],
                text=hit["entity"]["text"],
                score=hit["distance"],
            )
        )

    return SearchResponse(hits=hits)
