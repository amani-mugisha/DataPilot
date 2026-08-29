from __future__ import annotations

from pathlib import Path
from typing import BinaryIO
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from apps.importer.excel_formats import get_excel_format

from .base_writer import BaseWriter


class ExcelWriter(BaseWriter):
    """
    Write pandas DataFrames to supported Excel workbook formats.

    Exportable formats:

        .xlsx
        .xlsm
        .xltx
        .xltm

    Non-exportable formats:

        .xlsb
        .xlam
    """

    format_name = "excel"

    _CONTENT_TYPES = {
        ".xlsx": (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet.main+xml"
        ),
        ".xlsm": (
            "application/vnd.ms-excel.sheet.macroEnabled.main+xml"
        ),
        ".xltx": (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.template.main+xml"
        ),
        ".xltm": (
            "application/vnd.ms-excel.template.macroEnabled.main+xml"
        ),
    }

    def write(
        self,
        dataframe: pd.DataFrame,
        output_path: str | Path,
        **kwargs,
    ) -> Path:
        """
        Write a DataFrame to the requested Excel format.

        The output extension determines the Excel format.

        Additional keyword arguments are passed to pandas
        ``DataFrame.to_excel``.
        """

        if dataframe is None:
            raise ValueError(
                "ExcelWriter.write() requires a DataFrame."
            )

        path = Path(output_path)

        extension = path.suffix.lower()

        if not extension:
            raise ValueError(
                "Excel output filename must have an extension."
            )

        excel_format = get_excel_format(
            extension
        )

        if not excel_format.exportable:
            raise ValueError(
                f"Excel format {extension} "
                f"is not supported for export."
            )

        writer_engine = excel_format.writer_engine

        if writer_engine is None:
            raise ValueError(
                f"Excel format {extension} "
                f"does not have an export engine."
            )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        dataframe.to_excel(
            path,
            index=False,
            engine=writer_engine,
            **kwargs,
        )

        if extension != ".xlsx":
            self._set_content_type(
                path,
                extension,
            )

        return path

    @classmethod
    def _set_content_type(
        cls,
        path: Path,
        extension: str,
    ) -> None:
        """
        Update the OOXML workbook content type to match the
        requested Excel format.

        pandas/openpyxl creates the workbook package using the
        standard spreadsheet content type. Template and
        macro-enabled formats require their corresponding
        content type.
        """

        content_type = cls._CONTENT_TYPES.get(
            extension
        )

        if content_type is None:
            raise ValueError(
                f"Unsupported Excel content type: {extension}"
            )

        temporary_path = path.with_suffix(
            path.suffix + ".tmp"
        )

        try:
            with ZipFile(
                path,
                "r",
            ) as source:

                with ZipFile(
                    temporary_path,
                    "w",
                    compression=ZIP_DEFLATED,
                ) as target:

                    for item in source.infolist():

                        data = source.read(
                            item.filename
                        )

                        if item.filename == "[Content_Types].xml":
                            data = cls._replace_workbook_content_type(
                                data,
                                content_type,
                            )

                        target.writestr(
                            item,
                            data,
                        )

            temporary_path.replace(path)

        except Exception:
            temporary_path.unlink(
                missing_ok=True
            )
            raise

    @staticmethod
    def _replace_workbook_content_type(
        data: bytes,
        content_type: str,
    ) -> bytes:
        """
        Replace the workbook Override content type in
        [Content_Types].xml.
        """

        import re

        text = data.decode(
            "utf-8"
        )

        pattern = re.compile(
            r'(<Override\s+PartName="/xl/workbook\.xml"\s+'
            r'ContentType=")[^"]+(")'
        )

        updated, replacements = pattern.subn(
            rf'\g<1>{content_type}\g<2>',
            text,
            count=1,
        )

        if replacements != 1:
            raise ValueError(
                "Excel workbook content type could not be updated."
            )

        return updated.encode(
            "utf-8"
        )
