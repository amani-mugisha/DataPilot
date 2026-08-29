from __future__ import annotations

from .base_writer import BaseWriter
from .csv_writer import CSVWriter
from .excel_writer import ExcelWriter
from .pdf_writer import PDFWriter


WRITERS: dict[str, BaseWriter] = {
    "csv": CSVWriter(),
    "pdf": PDFWriter(),

    "xlsx": ExcelWriter(),
    "xlsm": ExcelWriter(),
    "xltx": ExcelWriter(),
    "xltm": ExcelWriter(),
}


def get_writer(file_format: str) -> BaseWriter:
    """
    Return the writer responsible for an export format.
    """

    try:
        return WRITERS[file_format]

    except KeyError as exc:
        raise ValueError(
            f"No writer registered for format: {file_format}"
        ) from exc