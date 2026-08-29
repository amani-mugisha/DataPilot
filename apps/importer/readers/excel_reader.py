from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from .base_reader import BaseReader
from ..excel_formats import get_excel_format


class ExcelReader(BaseReader):
    """
    Reader responsible for loading supported Excel workbooks
    into pandas DataFrames.
    """

    format_name = "excel"

    def read(
        self,
        file_path: str | Path | BinaryIO,
        *,
        filename: str | None = None,
        sheet_name: str | int = 0,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Read an Excel workbook sheet into a DataFrame.

        Args:
            file_path:
                Filesystem path or file-like object.

            filename:
                Original filename. Required when file_path is
                a file-like object.

            sheet_name:
                Sheet name or zero-based sheet index.

            **kwargs:
                Additional pandas read_excel options.
        """

        extension = self._get_extension(
            file_path,
            filename,
        )

        excel_format = get_excel_format(
            extension
        )

        engine = excel_format.reader_engine

        if engine is None:
            raise ValueError(
                f"Excel format {extension} cannot be imported as a dataset."
            )

        try:
            dataframe = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                engine=engine,
                **kwargs,
            )

        except ValueError as exc:
            raise ValueError(
                f"Could not read Excel file: {exc}"
            ) from exc

        except ImportError as exc:
            raise ValueError(
                f"The required Excel reader dependency "
                f"for {extension} is not installed."
            ) from exc

        except Exception as exc:
            raise ValueError(
                f"Could not read Excel file: {exc}"
            ) from exc

        if dataframe.empty and len(dataframe.columns) == 0:
            raise ValueError(
                "The Excel sheet does not contain any data."
            )

        return dataframe

    def list_sheets(
        self,
        file_path: str | Path | BinaryIO,
        *,
        filename: str | None = None,
    ) -> list[str]:
        """
        Return the names of all worksheets in an Excel workbook.
        """

        extension = self._get_extension(
            file_path,
            filename,
        )

        excel_format = get_excel_format(
            extension
        )

        engine = excel_format.reader_engine

        if engine is None:
            raise ValueError(
                f"Excel format {extension} cannot be inspected as a workbook."
            )

        try:
            workbook = pd.ExcelFile(
                file_path,
                engine=engine,
            )

            return workbook.sheet_names

        except ImportError as exc:
            raise ValueError(
                f"The required Excel reader dependency "
                f"for {extension} is not installed."
            ) from exc

        except Exception as exc:
            raise ValueError(
                f"Could not inspect Excel workbook: {exc}"
            ) from exc

    @staticmethod
    def _get_extension(
        file_path: str | Path | BinaryIO,
        filename: str | None,
    ) -> str:
        """
        Determine the extension of an Excel file.
        """

        if filename:
            return Path(filename).suffix.lower()

        if isinstance(file_path, (str, Path)):
            return Path(file_path).suffix.lower()

        raise ValueError(
            "filename is required for Excel file-like objects."
        )