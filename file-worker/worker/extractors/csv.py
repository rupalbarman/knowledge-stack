import asyncio
import csv
import io

from worker.extractors.base import ExtractionError, escape_table_cell


def _extract_sync(data: bytes) -> str:
    try:
        # utf-8-sig transparently strips a BOM if present (Excel CSVs)
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


async def extract(name: str, data: bytes) -> str:
    content = await asyncio.to_thread(_extract_sync, data)
    return f"{name}\n\n{content}"
