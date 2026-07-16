from typing import Protocol


class UnsupportedFileTypeError(Exception):
    """Raised when a file's extension has no registered extractor. Not
    retryable - the file type won't change on a retry."""


class ExtractionError(Exception):
    """Raised when a file matched a supported extension but its content
    couldn't actually be extracted (e.g. bad encoding). Not retryable."""


class Extractor(Protocol):
    async def __call__(self, name: str, data: bytes) -> str: ...


def escape_table_cell(value: str) -> str:
    """Shared by any extractor that builds a markdown pipe-table (csv,
    docx, ...). Pipe-table cells can't contain a raw "|" (the delimiter)
    or a raw newline - a CSV/DOCX cell can legitimately contain either.
    Order matters for the newline replacements: CRLF first, so a paired
    \\r\\n becomes one <br> instead of two."""
    return (
        value.replace("|", "\\|")
        .replace("\r\n", "<br>")
        .replace("\n", "<br>")
        .replace("\r", "<br>")
    )
