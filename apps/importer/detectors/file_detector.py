from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..formats import SUPPORTED_FORMATS


@dataclass(frozen=True)
class DetectedFile:
    """
    Metadata describing a detected DataPilot file.
    """

    filename: str
    extension: str
    format: str
    mime_type: str | None = None


def detect_file(
    filename: str,
    mime_type: str | None = None,
) -> DetectedFile:
    """
    Detect the logical DataPilot format from the filename.

    Detection is based primarily on the file extension.

    Examples:
        customers.csv  -> csv
        customers.xlsx -> excel_standard
        report.xlsm    -> excel_macro
        data.xlsb      -> excel_binary

    Raises:
        ValueError:
            If the filename has no extension or the extension
            is not supported by DataPilot.
    """

    if not filename:
        raise ValueError(
            "File has no extension."
        )

    extension = Path(filename).suffix.lower()

    if not extension:
        raise ValueError(
            "File has no extension."
        )

    file_format = SUPPORTED_FORMATS.get(extension)

    if file_format is None:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )

    return DetectedFile(
        filename=filename,
        extension=extension,
        format=file_format,
        mime_type=mime_type,
    )