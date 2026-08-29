from __future__ import annotations

from .base_reader import BaseReader
from .csv_reader import CSVReader
from .excel_reader import ExcelReader


READERS: dict[str, BaseReader] = {
    "csv": CSVReader(),

    "excel_standard": ExcelReader(),
    "excel_macro": ExcelReader(),
    "excel_template": ExcelReader(),
    "excel_template_macro": ExcelReader(),
    "excel_binary": ExcelReader(),
}


def get_reader(format_type: str) -> BaseReader:
    """
    Return the reader responsible for a DataPilot format.
    """

    try:
        return READERS[format_type]

    except KeyError as exc:
        raise ValueError(
            f"No reader registered for format: {format_type}"
        ) from exc