from langchain_text_splitters import RecursiveCharacterTextSplitter

from worker.config import settings


def _chunk_sync(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=overlap or settings.chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    return splitter.split_text(text)


async def chunk(text: str) -> list[str]:
    return _chunk_sync(text)
