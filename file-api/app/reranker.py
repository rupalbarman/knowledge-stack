import httpx

from app.config import settings
from app.models import RerankerItem


async def rerank(query: str, texts: list[str]) -> list[RerankerItem]:
    if not texts:
        return []

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            settings.reranker_url,
            headers={"Authorization": f"Bearer {settings.reranker_api_key}"},
            json={"model": settings.reranker_model, "query": query, "texts": texts},
        )
        response.raise_for_status()
        payload = response.json()

    items: list[RerankerItem] = []
    for raw in payload:
        item = RerankerItem.model_validate(raw)
        items.append(item)

    return items
