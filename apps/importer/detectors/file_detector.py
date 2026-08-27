from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DetectedFile:
    filename: str
    extension: str
    format: str
    mime_type: str | None = None


SUPPORTED_FORMATS = {
    ".csv": "csv",
}


def detect_file(
    filename: str,
    mime_type: str | None = None,
) -> DetectedFile:
    """
    Detect the logical file format from the uploaded filename.

    DataPilot currently supports CSV files only.
    """

    extension = Path(filename).suffix.lower()

    file_format = SUPPORTED_FORMATS.get(extension)

    if not file_format:
        raise ValueError(
            f"Unsupported file format: "
            f"{extension or 'unknown'}"
        )

    return DetectedFile(
        filename=filename,
        extension=extension,
        format=file_format,
        mime_type=mime_type,
    )