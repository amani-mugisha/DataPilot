from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExcelFormat:
    extension: str
    format_type: str
    reader_engine: str | None
    writer_engine: str | None
    exportable: bool
    macro_enabled: bool = False
    template: bool = False
    addin: bool = False


EXCEL_FORMATS: dict[str, ExcelFormat] = {
    ".xlsx": ExcelFormat(
        extension=".xlsx",
        format_type="excel_standard",
        reader_engine="openpyxl",
        writer_engine="openpyxl",
        exportable=True,
    ),

    ".xlsm": ExcelFormat(
        extension=".xlsm",
        format_type="excel_macro",
        reader_engine="openpyxl",
        writer_engine="openpyxl",
        exportable=True,
        macro_enabled=True,
    ),

    ".xltx": ExcelFormat(
        extension=".xltx",
        format_type="excel_template",
        reader_engine="openpyxl",
        writer_engine="openpyxl",
        exportable=True,
        template=True,
    ),

    ".xltm": ExcelFormat(
        extension=".xltm",
        format_type="excel_template_macro",
        reader_engine="openpyxl",
        writer_engine="openpyxl",
        exportable=True,
        macro_enabled=True,
        template=True,
    ),

    ".xlsb": ExcelFormat(
        extension=".xlsb",
        format_type="excel_binary",
        reader_engine="pyxlsb",
        writer_engine=None,
        exportable=False,
    ),

    ".xlam": ExcelFormat(
        extension=".xlam",
        format_type="excel_addin",
        reader_engine=None,
        writer_engine=None,
        exportable=False,
        macro_enabled=True,
        addin=True,
    ),
}


def get_excel_format(extension: str) -> ExcelFormat:
    """
    Return metadata for a supported Excel extension.
    """

    normalized = extension.strip().lower()

    try:
        return EXCEL_FORMATS[normalized]

    except KeyError as exc:
        raise ValueError(
            f"Unsupported Excel extension: {normalized}"
        ) from exc


def supported_excel_extensions() -> tuple[str, ...]:
    """
    Return all supported Excel extensions.
    """

    return tuple(EXCEL_FORMATS.keys())


def exportable_excel_extensions() -> tuple[str, ...]:
    """
    Return Excel extensions DataPilot can currently export.
    """

    return tuple(
        extension
        for extension, excel_format in EXCEL_FORMATS.items()
        if excel_format.exportable
    )