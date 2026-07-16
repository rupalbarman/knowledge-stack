import re

from worker.chunkers.recursive import _chunk_sync
from worker.config import settings

# Splits blocks with a double newline separator - with an optional whitespace. For example \n\s\s\s\s\n
_BLOCK_SPLIT = re.compile(r"\n\s*\n")

# Matches atomic blocks such as <table> and <figure> - courtesy of pdf_ocr OCR VL model (Typhoon)
_ATOMIC_BLOCK = re.compile(r"^<(table|figure)>.*</\1>$", re.DOTALL)

# Within a block, search for atomic blocks if present, when _BLOCK_SPLIT is not atomic enough
_ATOMIC_TAG_SEARCH = re.compile(r"<(table|figure)>.*?</\1>", re.DOTALL)

# Markdown table separator row between header and data rows
_SEPARATOR_ROW = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$")

# How much of the preceding chunk to carry forward as context for a table/figure
# that follows it - e.g. a table's caption/title, which usually
# lives in the paragraph right before it, not inside the table itself.
_MAX_CAPTION_LEN = 300


def _split_out_atomic_tags(block: str) -> list[str]:
    """Sometimes each block is not atomic enough since the model does not insert a blank line (\n\n)
    between a caption and the <table> or <figure>. For instance = this is a figure\n<table>.
    So this function takes a block and splits it further.
    """
    pieces = []
    pos = 0
    for m in _ATOMIC_TAG_SEARCH.finditer(block):
        before = block[pos : m.start()].strip()
        if before:
            pieces.append(before)
        pieces.append(m.group(0))
        pos = m.end()
    remainder = block[pos:].strip()
    if remainder:
        pieces.append(remainder)
    return pieces or [block]


# Utility to identify if block is a markdown table with | operators
def _is_pipe_table(block: str) -> bool:
    lines = [line for line in block.splitlines() if line.strip()]
    return len(lines) >= 2 and all(line.strip().startswith("|") for line in lines)


def _recent_caption(chunks: list[str]) -> str:
    if not chunks:
        return ""
    last = chunks[-1]
    if _is_pipe_table(last) or _ATOMIC_BLOCK.match(last):
        return ""
    return last[-_MAX_CAPTION_LEN:]


def _split_pipe_table(block: str, chunk_size: int, caption: str = "") -> list[str]:
    """
    pdf.py extractor spits out github markdown tables. This is also considered an atomic block
    just like the <table> and <figure>. We ensure that mid-table chunk breaks are avoided and if done,
    we include the table header and its title / caption to every table chunk.
    """
    lines = [line for line in block.splitlines() if line.strip()]
    header = lines[:1]
    if len(lines) > 1 and _SEPARATOR_ROW.match(lines[1].strip()):
        header = lines[:2]
    rows = lines[len(header) :]

    prefix = f"{caption}\n\n" if caption else ""
    header_text = "\n".join(header)

    whole = "\n".join(lines)
    if len(prefix) + len(whole) <= chunk_size:
        return [f"{prefix}{whole}"]

    fragments = []
    current = list(header)
    current_len = len(prefix) + len(header_text)
    for row in rows:
        if current_len + len(row) + 1 > chunk_size and len(current) > len(header):
            fragments.append(prefix + "\n".join(current))
            current = list(header)
            current_len = len(prefix) + len(header_text)
        current.append(row)
        current_len += len(row) + 1

    if len(current) > len(header):
        fragments.append(prefix + "\n".join(current))
    elif not fragments:
        fragments.append(f"{prefix}{header_text}")

    return fragments


async def chunk(text: str) -> list[str]:
    """Packs Markdown blocks (paragraphs, tables, figures) up to
    chunk_size, preferring to split between blocks rather than within one.
    Tables get row-level awareness: a table too big for one chunk splits
    at row boundaries with its header repeated in every fragment, instead
    of being cut mid-row like a plain character-offset split would.

    There's no overlap between packed blocks - overlap
    is only applied within a single oversized block that falls back to
    recursive splitting."""
    chunk_size = settings.chunk_size
    overlap = settings.chunk_overlap

    blocks = []
    for raw_block in _BLOCK_SPLIT.split(text):
        raw_block = raw_block.strip()
        if raw_block:
            blocks.extend(_split_out_atomic_tags(raw_block))

    chunks: list[str] = []
    buffer: list[str] = []
    buffer_len = 0

    def flush() -> None:
        nonlocal buffer, buffer_len
        if buffer:
            chunks.append("\n\n".join(buffer))
        buffer = []
        buffer_len = 0

    for block in blocks:
        if _ATOMIC_BLOCK.match(block):
            flush()
            caption = _recent_caption(chunks)
            chunks.append(f"{caption}\n\n{block}" if caption else block)
            continue

        if _is_pipe_table(block):
            flush()
            caption = _recent_caption(chunks)
            chunks.extend(_split_pipe_table(block, chunk_size, caption))
            continue

        if len(block) > chunk_size:
            flush()
            chunks.extend(_chunk_sync(block, chunk_size, overlap))
            continue

        if buffer_len + len(block) + 2 > chunk_size:
            flush()

        buffer.append(block)
        buffer_len += len(block) + 2

    flush()

    return chunks
