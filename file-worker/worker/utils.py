import logging
from pathlib import Path
from uuid import UUID

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent


def chunked[T](items: list[T], size: int) -> list[list[T]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def save_to_temp_dir(file_id: UUID | str, content: str) -> None:
    try:
        temp_dir = ROOT / "tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path = temp_dir / f"{file_id}.txt"
        file_path.write_text(content, encoding="utf-8")
    except Exception as e:
        logger.warning("unable to write to temp file: %s", e)
