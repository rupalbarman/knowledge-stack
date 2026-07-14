import httpx

from worker.config import settings
from worker.utils import chunked


async def _embed_batch(client: httpx.AsyncClient, texts: list[str]) -> list[list[float]]:
    response = await client.post(
        settings.embeddings_url,
        headers={"Authorization": f"Bearer {settings.embeddings_api_key}"},
        json={"model": settings.embeddings_model, "inputs": texts},
    )
    response.raise_for_status()
    return response.json()


async def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    vectors: list[list[float]] = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for batch in chunked(texts, settings.embeddings_batch_size):
            vectors.extend(await _embed_batch(client, batch))

    return vectors
