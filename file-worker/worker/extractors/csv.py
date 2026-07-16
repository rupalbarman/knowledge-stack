import asyncio
import csv
import io

from worker.extractors.base import (
    ExtractionError,
    escape_table_cell,
    rows_to_markdown_table,
)


def _extract_sync(data: bytes) -> str:
    try:
        # utf-8-sig strips a BOM if present (Excel CSVs)
        # and behaves exactly like utf-8 otherwise.
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ExtractionError(f"could not decode as utf-8 text: {exc}") from exc

    try:
        rows = [
            [escape_table_cell(cell) for cell in row]
            for row in csv.reader(io.StringIO(text))
        ]
    except csv.Error as exc:
        raise ExtractionError(f"could not parse CSV: {exc}") from exc

    return rows_to_markdown_table(rows)


async def extract(name: str, data: bytes) -> str:
    content = await asyncio.to_thread(_extract_sync, data)
    return f"{name}\n\n{content}"
