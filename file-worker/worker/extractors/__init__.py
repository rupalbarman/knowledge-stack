from pathlib import Path

from worker.extractors import csv, docx, pdf, pptx, text
from worker.extractors.base import ExtractionError, Extractor, UnsupportedFileTypeError

# Keyed by extension rather than the upload's reported content_type - that
# header is client-supplied and unreliable (e.g. often defaults to
# application/octet-stream for plain text). Extend this as new formats land
# behind their own extractors/<format>.py.
_BY_EXTENSION: dict[str, Extractor] = {
    ".txt": text.extract,
    ".pdf": pdf.extract,
    ".md": pdf.extract,
    ".epub": pdf.extract,
    ".mobi": pdf.extract,
    ".csv": csv.extract,
    ".docx": docx.extract,
    ".pptx": pptx.extract,
}


def get_extractor(filename: str) -> Extractor:
    ext = Path(filename).suffix.lower()
    extractor = _BY_EXTENSION.get(ext)
    if extractor is None:
        raise UnsupportedFileTypeError(
            f"unsupported file type: {ext or '(no extension)'}"
        )
    return extractor


__all__ = ["get_extractor", "ExtractionError", "UnsupportedFileTypeError"]
