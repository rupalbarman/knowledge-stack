from worker.config import settings


def chunk_text(
    text: str, chunk_size: int | None = None, overlap: int | None = None
) -> list[str]:
    chunk_size = chunk_size if chunk_size is not None else settings.chunk_size
    overlap = overlap if overlap is not None else settings.chunk_overlap

    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == text_length:
            break
        start = end - overlap

    return chunks
