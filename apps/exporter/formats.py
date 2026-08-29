from __future__ import annotations


SUPPORTED_EXPORT_FORMATS = {
    "csv",
    "pdf",
    "xlsx",
    "xlsm",
    "xltx",
    "xltm",
}


EXCEL_EXPORT_FORMATS = {
    "xlsx",
    "xlsm",
    "xltx",
    "xltm",
}


def normalize_export_format(
    file_format: str,
) -> str:
    """
    Normalize and validate an export format.
    """

    if not isinstance(file_format, str):
        raise ValueError(
            "Export format must be a string."
        )

    normalized = file_format.strip().lower()

    if not normalized:
        raise ValueError(
            "Export format cannot be empty."
        )

    if normalized not in SUPPORTED_EXPORT_FORMATS:
        raise ValueError(
            f"Unsupported export format "
            f"'{normalized}'."
        )

    return normalized


def is_excel_export_format(
    file_format: str,
) -> bool:
    """
    Return whether the format is an Excel export format.
    """

    return file_format in EXCEL_EXPORT_FORMATS