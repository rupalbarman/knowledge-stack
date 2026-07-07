from worker.extractors.base import ExtractionError


def extract(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExtractionError(f"could not decode as utf-8 text: {exc}") from exc
