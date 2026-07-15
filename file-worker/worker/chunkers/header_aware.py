import re

from worker.chunkers.markdown import (
    _ATOMIC_BLOCK,
    _BLOCK_SPLIT,
    _is_pipe_table,
    _split_out_atomic_tags,
    _split_pipe_table,
)
from worker.chunkers.recursive import _chunk_sync
from worker.config import settings

# Markdown ATX heading (# through ######)
_HEADING = re.compile(r"^#{1,6}\s")

# How much of the immediately preceding plain-text content to carry into a
# table/figure as a caption, on top of the section heading - a table's own
# caption is often a plain paragraph ("Table 1. ..."), not a markdown
# heading, so the section heading alone doesn't capture it.
_MAX_CAPTION_LEN = 300


def _has_content(section: list[str]) -> bool:
    return any(not _HEADING.match(b) for b in section)


def _split_into_sections(blocks: list[str]) -> list[list[str]]:
    """Groups blocks by heading instead of by size. A new section only
    starts at a heading if the current section already has non-heading
    content - so stacked headings (a heading immediately followed by
    another heading, or by a stray short block, before any real content)
    chain into the same section rather than each becoming a fragment of
    their own. This is what makes a heading structurally unable to end up
    separated from what it introduces: unlike a size-based packer that
    flushes reactively and can be defeated by something unexpected sitting
    in between, sectioning happens first here - a heading and its content
    are the same unit from the start, regardless of what's in between."""
    sections: list[list[str]] = []
    current: list[str] = []

    for block in blocks:
        if _HEADING.match(block) and _has_content(current):
            sections.append(current)
            current = [block]
        else:
            current.append(block)

    if current:
        sections.append(current)

    return sections


def _split_section_header(section: list[str]) -> tuple[list[str], list[str]]:
    i = 0
    while i < len(section) and _HEADING.match(section[i]):
        i += 1
    return section[:i], section[i:]


def _pack_section(section: list[str], chunk_size: int, overlap: int) -> list[str]:
    """Size-bounds one heading's section. Unlike markdown.py's single pass,
    the section's header is known up front (not guessed from whatever
    chunk happened to precede it) and is repeated across every chunk this
    section produces - including table/figure fragments - not just the
    first, so a heavily-split section still carries its heading in every
    piece.

    A table/figure also picks up whatever plain-text content was flushed
    right before it in this section, same as markdown.py's caption
    lookup - the section heading gives broad context ("under 4.1 ..."),
    the immediate caption gives the specific one ("Table 1: ...")."""
    header_blocks, body_blocks = _split_section_header(section)
    header_text = "\n\n".join(header_blocks)
    prefix = f"{header_text}\n\n" if header_text else ""

    if not body_blocks:
        return [header_text] if header_text else []

    chunks: list[str] = []
    buffer: list[str] = []
    buffer_len = len(prefix)
    # tail of the last plain content flushed in this section - reset (not
    # updated) after a table/figure, so one never inherits another's
    # content as its "caption" when they sit back to back.
    last_flushed = ""

    def flush() -> None:
        nonlocal buffer, buffer_len, last_flushed
        if buffer:
            body = "\n\n".join(buffer)
            chunks.append(prefix + body)
            last_flushed = body
        buffer = []
        buffer_len = len(prefix)

    def combined_caption() -> str:
        caption = last_flushed[-_MAX_CAPTION_LEN:] if last_flushed else ""
        return "\n\n".join(p for p in (header_text, caption) if p)

    for block in body_blocks:
        if _ATOMIC_BLOCK.match(block):
            flush()
            combined = combined_caption()
            chunks.append(f"{combined}\n\n{block}" if combined else block)
            last_flushed = ""
            continue

        if _is_pipe_table(block):
            flush()
            chunks.extend(_split_pipe_table(block, chunk_size, combined_caption()))
            last_flushed = ""
            continue

        if len(prefix) + len(block) > chunk_size:
            flush()
            budget = max(chunk_size - len(prefix), 1)
            for piece in _chunk_sync(block, budget, overlap):
                chunks.append(f"{prefix}{piece}" if prefix else piece)
            last_flushed = ""
            continue

        if buffer_len + len(block) + 2 > chunk_size:
            flush()

        buffer.append(block)
        buffer_len += len(block) + 2

    flush()

    return chunks


async def chunk(text: str) -> list[str]:
    """Preserves headers along with their content. Leverages block splitting and
    atomic block detection from markdown.py. Then arranges those blocks into sections.

    Every chunk in a section carries that section's heading. A table/figure
    additionally picks up its own immediate preceding caption paragraph
    (see _pack_section's combined_caption), the same lookup markdown.py
    does - so both the broad section context and the specific caption are
    present, not just one or the other."""
    chunk_size = settings.chunk_size
    overlap = settings.chunk_overlap

    blocks = []
    for raw_block in _BLOCK_SPLIT.split(text):
        raw_block = raw_block.strip()
        if raw_block:
            blocks.extend(_split_out_atomic_tags(raw_block))

    sections = _split_into_sections(blocks)

    chunks: list[str] = []
    for section in sections:
        chunks.extend(_pack_section(section, chunk_size, overlap))

    return chunks
