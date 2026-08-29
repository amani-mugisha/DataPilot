from __future__ import annotations

from .base_validator import BaseValidator
from .csv_validator import CSVValidator
from .excel_validator import ExcelValidator


VALIDATORS: dict[str, BaseValidator] = {
    "csv": CSVValidator(),

    "excel_standard": ExcelValidator(),
    "excel_macro": ExcelValidator(),
    "excel_template": ExcelValidator(),
    "excel_template_macro": ExcelValidator(),
    "excel_binary": ExcelValidator(),

    # Recognized and validated, but not imported as DataFrame.
    "excel_addin": ExcelValidator(),
}


def get_validator(format_type: str) -> BaseValidator:
    """
    Return the validator responsible for a DataPilot format.
    """

    try:
        return VALIDATORS[format_type]

    except KeyError as exc:
        raise ValueError(
            f"No validator registered for format: {format_type}"
        ) from exc