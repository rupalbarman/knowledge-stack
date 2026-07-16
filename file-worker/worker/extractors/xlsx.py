import asyncio
import io

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

from worker.extractors.base import (
    ExtractionError,
    escape_table_cell,
    rows_to_markdown_table,
)


def _cell_to_str(value: object) -> str:
    if value is None:
        return ""
    return escape_table_cell(str(value))


def _non_empty_cells(row: tuple) -> list[object]:
    return [cell for cell in row if cell is not None and str(cell).strip()]


def _sheet_to_markdown(sheet: Worksheet) -> str:
    """
    Parse the sheet to differentiate text content and table content.
    - Single row, single cell content gets assumed as text / caption
    - Contiguous multi-cell rows are considered a table
    - Empty row is used to end the parse and signals a end of a table
    """
    blocks = []
    table_rows: list[list[str]] = []

    def flush_table() -> None:
        if table_rows:
            table = rows_to_markdown_table(table_rows)
            if table:
                blocks.append(table)
            table_rows.clear()

    for row in sheet.iter_rows(values_only=True):
        non_empty = _non_empty_cells(row)

        if len(non_empty) > 1:
            table_rows.append([_cell_to_str(cell) for cell in row])
            continue

        flush_table()

        if len(non_empty) == 1:
            blocks.append(escape_table_cell(str(non_empty[0])))

    flush_table()

    if not blocks:
        return ""
    return f"# {sheet.title}\n\n" + "\n\n".join(blocks)


def _extract_sync(data: bytes) -> str:
    try:
        workbook = openpyxl.load_workbook(
            io.BytesIO(data),
            data_only=True,
            read_only=True,
        )
    except Exception as exc:
        raise ExtractionError(f"could not parse XLSX: {exc}") from exc

    sheets = [_sheet_to_markdown(workbook[name]) for name in workbook.sheetnames]
    return "\n\n".join(sheet for sheet in sheets if sheet)


async def extract(name: str, data: bytes) -> str:
    return await asyncio.to_thread(_extract_sync, data)
