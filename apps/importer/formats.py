from __future__ import annotations


SUPPORTED_FORMATS = {
    ".csv": "csv",

    ".xlsx": "excel_standard",
    ".xlsm": "excel_macro",
    ".xlsb": "excel_binary",

    ".xltx": "excel_template",
    ".xltm": "excel_template_macro",

    ".xlam": "excel_addin",
}


READABLE_FORMATS = {
    "csv",
    "excel_standard",
    "excel_macro",
    "excel_binary",
    "excel_template",
    "excel_template_macro",
}


EXPORTABLE_FORMATS = {
    "csv",
    "excel_standard",
    "excel_macro",
}