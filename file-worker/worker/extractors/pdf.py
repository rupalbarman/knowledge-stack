import asyncio
import logging

import pymupdf
import pymupdf4llm

from worker.config import settings
from worker.extractors.base import ExtractionError
from worker.extractors.pdf_ocr import extract as ocr_extract

logger = logging.getLogger(__name__)

# Cut-off amount of actual content (not raw text length) to switch to OCR
# if available
_MIN_TEXT_LENGTH = 20


def _content_length(text: str) -> int:
    # Counts only letters/digits, not raw string length and str.isalnum()
    # is Unicode-aware
    return sum(1 for c in text if c.isalnum())


def _extract_sync(data: bytes) -> str:
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        text = pymupdf4llm.to_markdown(
            doc,
            use_ocr=False,
            embed_images=False,
            write_images=False,
            ignore_images=True,
            header=False,
            footer=False,
        )
        return f"{text}"


async def extract(data: bytes) -> str:
    try:
        text = await asyncio.to_thread(_extract_sync, data)
        parse_error = None
    except Exception as exc:
        text = None
        parse_error = exc

    if parse_error is None and text and _content_length(text) >= _MIN_TEXT_LENGTH:
        return text

    if not settings.ocr_url:
        if parse_error is not None or not text:
            raise ExtractionError(
                f"could not parse PDF: {parse_error}"
            ) from parse_error
        return text

    if parse_error is not None:
        logger.info("could not parse PDF (%s), falling back to OCR", parse_error)
    else:
        logger.info(
            f"PDF yielded less than {_MIN_TEXT_LENGTH} letter/digit char(s), "
            "falling back to OCR"
        )

    return await ocr_extract(data)
