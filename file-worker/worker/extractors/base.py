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
    docx, pptx, ...). Pipe-table cells can't contain a raw "|" (the
    delimiter) or a raw newline - a CSV/DOCX/PPTX cell can legitimately
    contain either. Order matters for the newline replacements: CRLF
    first, so a paired \\r\\n becomes one <br> instead of two."""
    return (
        value.replace("|", "\\|")
        .replace("\r\n", "<br>")
        .replace("\n", "<br>")
        .replace("\r", "<br>")
    )


def rows_to_markdown_table(rows: list[list[str]]) -> str:
    """Builds a markdown pipe-table from already-escaped cell values
    (see escape_table_cell). Blank rows are dropped, and every row is
    padded/truncated to the header row's column count."""
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        return ""

    header, *data_rows = rows
    col_count = len(header)

    lines = [
        "|" + "|".join(header) + "|",
        "|" + "|".join(["---"] * col_count) + "|",
    ]
    for row in data_rows:
        padded = (row + [""] * col_count)[:col_count]
        lines.append("|" + "|".join(padded) + "|")

    return "\n".join(lines)
