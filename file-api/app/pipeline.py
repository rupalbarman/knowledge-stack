import logging
from uuid import UUID

from asyncpg import Pool
from pymilvus import AsyncMilvusClient

from app.config import settings
from app.models import SearchHit, SearchOptions, SearchRequest
from app.reranker import rerank
from app.retriever import RETRIEVERS

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self, pool: Pool, milvus: AsyncMilvusClient) -> None:
        retriever_cls = RETRIEVERS.get("single")
        if not retriever_cls:
            raise Exception("retriever not found")

        self.retriever = retriever_cls(pool=pool, milvus=milvus)

    async def retrieve(
        self, request: SearchRequest, project_id: UUID, filter_expr: str
    ) -> list[SearchHit]:
        options = request.options or SearchOptions()
        hits = await self.retriever.retrieve(request, project_id, filter_expr)

        if not settings.reranker_enabled:
            logger.debug("re-ranking disabled, returning retriever hits as-is")
            return hits

        try:
            ranked_texts = await rerank(
                query=request.query, texts=[hit.text for hit in hits]
            )
        except Exception:
            logger.warning(
                "reranker call failed, falling back to direct hits",
                exc_info=True,
            )
            return hits

        ranked_hits = []
        for text in ranked_texts:
            hit = hits[text.index]
            hit.score = text.score
            ranked_hits.append(hit)

        # min_score only applied when reranker is enabled since otherwise
        # the scores are wildly different for each mode
        if options.min_score is not None:
            ranked_hits = [hit for hit in ranked_hits if hit.score >= options.min_score]

        return ranked_hits
