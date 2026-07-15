from worker.chunkers import fixed_size, markdown
from worker.chunkers.base import Chunker, UnknownStrategyError

_BY_NAME: dict[str, Chunker] = {
    "fixed_size": fixed_size.chunk,
    "markdown": markdown.chunk,
}


def get_chunker(name: str) -> Chunker:
    chunker = _BY_NAME.get(name)
    if chunker is None:
        raise UnknownStrategyError(f"unknown chunking strategy: {name!r}")
    return chunker


__all__ = ["get_chunker", "UnknownStrategyError"]
