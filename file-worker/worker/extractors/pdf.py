import asyncio
import logging

import pymupdf

from worker.config import settings
from worker.extractors.base import ExtractionError
from worker.extractors.pdf_ocr import extract as ocr_extract

logger = logging.getLogger(__name__)

# Cut-off text length to switch to OCR if available
_MIN_TEXT_LENGTH = 20


def _extract_sync(data: bytes) -> str:
    texts = []
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            texts.append(page.get_text())
        return "\n\n".join(texts)


async def extract(data: bytes) -> str:
    try:
        text = await asyncio.to_thread(_extract_sync, data)
        parse_error = None
    except Exception as exc:
        text = None
        parse_error = exc

    if parse_error is None and text and len(text.strip()) >= _MIN_TEXT_LENGTH:
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
            f"PDF yielded less than {_MIN_TEXT_LENGTH} char(s) of text, falling back to OCR"
        )

    return await ocr_extract(data)
