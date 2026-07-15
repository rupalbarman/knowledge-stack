from worker.chunkers import header_aware, markdown, recursive
from worker.chunkers.base import Chunker, UnknownStrategyError

_BY_NAME: dict[str, Chunker] = {
    "recursive": recursive.chunk,
    "markdown": markdown.chunk,
    "header_aware": header_aware.chunk,
}


def get_chunker(name: str) -> Chunker:
    chunker = _BY_NAME.get(name)
    if chunker is None:
        raise UnknownStrategyError(f"unknown chunking strategy: {name!r}")
    return chunker


__all__ = ["get_chunker", "UnknownStrategyError"]
