from uuid import UUID

from asyncpg import Pool
from pymilvus import AnnSearchRequest, AsyncMilvusClient, RRFRanker

from app.config import settings
from app.embeddings import embed
from app.milvus_client import collection_name_for_project
from app.models import SearchHit, SearchOptions, SearchRequest
from app.repositories import files as files_repo


class BaseRetriever:
    def __init__(self, pool: Pool, milvus: AsyncMilvusClient) -> None:
        self.pool = pool
        self.milvus = milvus

    async def retrieve(
        self, request: SearchRequest, project_id: UUID, filter_expr: str
    ) -> list[SearchHit]:
        options = request.options or SearchOptions()
        top_k = options.top_k or settings.search_default_top_k
        assert len(filter_expr)

        collection = collection_name_for_project(project_id)

        if options.mode == "hybrid":
            vectors = await embed([request.query])
            dense_request = AnnSearchRequest(
                data=[vectors[0]],
                anns_field="dense",
                param={},
                limit=top_k,
                expr=filter_expr,
            )
            sparse_request = AnnSearchRequest(
                data=[request.query],
                anns_field="sparse",
                param={},
                limit=top_k,
                expr=filter_expr,
            )
            results = await self.milvus.hybrid_search(
                collection_name=collection,
                reqs=[dense_request, sparse_request],
                ranker=RRFRanker(),
                limit=top_k,
                output_fields=["file_id", "chunk_index", "text"],
            )
        else:
            if options.mode == "dense":
                vectors = await embed([request.query])
                query_data = [vectors[0]]
            else:
                query_data = [request.query]

            results = await self.milvus.search(
                collection_name=collection,
                data=query_data,
                anns_field=options.mode,
                filter=filter_expr,
                limit=top_k,
                output_fields=["file_id", "chunk_index", "text"],
            )
        raw_hits = results[0] if results else []

        if not raw_hits:
            return []

        file_ids = list({UUID(hit["entity"]["file_id"]) for hit in raw_hits})
        async with self.pool.acquire() as conn:
            files = await files_repo.list_by_ids(conn, project_id, file_ids)
        names_by_id = {f["id"]: f["name"] for f in files}

        hits = []
        for hit in raw_hits:
            file_id = UUID(hit["entity"]["file_id"])
            hits.append(
                SearchHit(
                    file_id=file_id,
                    # A hit can outlive its file if the delete-vectors cleanup
                    file_name=names_by_id.get(file_id, "(deleted file)"),
                    chunk_index=hit["entity"]["chunk_index"],
                    text=hit["entity"]["text"],
                    score=hit["distance"],
                )
            )
        return hits


RETRIEVERS: dict[str, type[BaseRetriever]] = {
    "single": BaseRetriever,
}
