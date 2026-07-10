import httpx

from worker.config import settings


async def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            settings.embeddings_url,
            headers={"Authorization": f"Bearer {settings.embeddings_api_key}"},
            json={"model": settings.embeddings_model, "inputs": texts},
        )
        response.raise_for_status()
        payload = response.json()

    return payload
