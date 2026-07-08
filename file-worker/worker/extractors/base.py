from typing import Protocol


class UnsupportedFileTypeError(Exception):
    """Raised when a file's extension has no registered extractor. Not
    retryable - the file type won't change on a retry."""


class ExtractionError(Exception):
    """Raised when a file matched a supported extension but its content
    couldn't actually be extracted (e.g. bad encoding). Not retryable."""


class Extractor(Protocol):
    def __call__(self, data: bytes) -> str: ...
