import asyncio
import base64
import logging

import httpx
import pymupdf
from pymupdf import csRGB

from worker.config import settings
from worker.extractors.base import ExtractionError

logger = logging.getLogger(__name__)

_MAX_DIMENSION = 1600  # long edge, in pixels
_CONCURRENCY = 5
_MAX_PAGES = 100
_MAX_TOKENS = 16384

_PROMPT = """
Extract all text from the image.


Instructions:
- Only return the clean Markdown.
- Do not include any explanation or extra text.
- You must include all information on the page.


Formatting Rules:
- Tables: Render tables using <table>...</table> in clean HTML format.
- Equations: Render equations using LaTeX syntax with inline ($...$) and block ($$...$$).
- Images/Charts/Diagrams: Wrap any clearly defined visual areas (e.g. charts, diagrams, pictures) in:


<figure>
Describe the image's main elements (people, objects, text), note any contextual clues (place, event, culture), mention visible text and its meaning, provide deeper analysis when relevant (especially for financial charts, graphs, or documents), comment on style or architecture if relevant, then give a concise overall summary. Describe in {figure_language}.
</figure>


- Page Numbers: Wrap page numbers in <page_number>...</page_number> (e.g., <page_number>14</page_number>).
- Check-boxes: Use ☐ for unchecked and ☑ for checked boxes.

""".format(figure_language="Thai")


def _render_page(page: pymupdf.Page) -> bytes:
    zoom = _MAX_DIMENSION / max(page.rect.width, page.rect.height)
    matrix = pymupdf.Matrix(zoom, zoom)
    pixel_map = page.get_pixmap(
        matrix=matrix,
        colorspace=csRGB,
        alpha=False,
        annots=False,
    )
    return pixel_map.tobytes("jpeg")


def _render_pages_sync(data: bytes) -> list[bytes]:
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        if len(doc) > _MAX_PAGES:
            raise ExtractionError(
                f"PDF has {len(doc)} pages, exceeding the {_MAX_PAGES}-page OCR limit"
            )
        return [_render_page(page) for page in doc]


async def _ocr_page(
    client: httpx.AsyncClient, semaphore: asyncio.Semaphore, image: bytes, index: int
) -> str:
    url = f"{settings.ocr_url}/chat/completions"
    img_b64 = base64.b64encode(image).decode("utf-8")
    payload = {
        "model": settings.ocr_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": _PROMPT,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                    },
                ],
            }
        ],
        "max_tokens": _MAX_TOKENS,
        "temperature": 0.0,
    }

    async with semaphore:
        response = await client.post(
            url,
            headers={"Authorization": f"Bearer {settings.ocr_api_key}"},
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

    try:
        choice = result["choices"][0]
        if choice.get("finish_reason") != "stop":
            logger.warning(
                "OCR page %d finished with reason=%r, output may be truncated",
                index,
                choice.get("finish_reason"),
            )
        return choice["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise ExtractionError(
            f"unexpected OCR response shape for page {index}: {exc}"
        ) from exc


async def extract(data: bytes) -> str:
    """OCR fallback for scanned/image-only PDFs. Renders each page to a
    JPEG and sends it to the OCR model, up to _CONCURRENCY requests in
    flight at once. A page that fails is replaced with a placeholder
    marker instead of aborting the whole document - losing one page
    shouldn't discard every other page's already-completed OCR. Order is
    preserved via each page's own index, independent of completion order."""
    try:
        images = await asyncio.to_thread(_render_pages_sync, data)
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(f"could not render PDF pages: {exc}") from exc

    semaphore = asyncio.Semaphore(_CONCURRENCY)
    logger.info("starting OCR extraction for %d page(s)", len(images))
    async with httpx.AsyncClient(verify=False, timeout=180.0) as client:
        results = await asyncio.gather(
            *(_ocr_page(client, semaphore, image, i) for i, image in enumerate(images)),
            return_exceptions=True,
        )

    pages = []
    failures = 0
    for i, result in enumerate(results):
        if isinstance(result, BaseException):
            logger.warning("OCR failed for page %d: %s", i, result)
            failures += 1
            pages.append(f"[OCR failed for page {i}: {result}]")
        else:
            pages.append(result)

    if failures == len(pages):
        raise ExtractionError("OCR failed for every page")

    return "\n\n".join(pages)
