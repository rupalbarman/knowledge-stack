from typing import Protocol


class UnknownStrategyError(Exception):
    """Raised when settings.chunking_strategy names a strategy that isn't
    registered. Not retryable - a bad config won't fix itself on retry."""


class Chunker(Protocol):
    async def __call__(self, text: str) -> list[str]: ...
