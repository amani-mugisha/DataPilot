from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from .base_reader import BaseReader


class CSVReader(BaseReader):
    """
    Reader responsible for loading CSV files into pandas DataFrames.

    CSV-specific parsing belongs here so that the rest of DataPilot
    does not need to know how CSV files are read.
    """

    format_name = "csv"

    def read(
        self,
        file_path: str | Path | BinaryIO,
    ) -> pd.DataFrame:
        """
        Read a CSV file into a DataFrame.

        Raises:
            ValueError: If the CSV cannot be read.
        """

        if file_path is None:
            raise ValueError(
                "CSVReader.read() requires a file."
            )

        try:
            dataframe = pd.read_csv(file_path)

        except pd.errors.EmptyDataError as exc:
            raise ValueError(
                "The CSV file is empty."
            ) from exc

        except pd.errors.ParserError as exc:
            raise ValueError(
                "The CSV file could not be parsed. "
                "Please check its structure and delimiters."
            ) from exc

        except UnicodeDecodeError as exc:
            raise ValueError(
                "The CSV file encoding could not be read."
            ) from exc

        except Exception as exc:
            raise ValueError(
                f"Could not read CSV file: {exc}"
            ) from exc

        if dataframe.empty and len(dataframe.columns) == 0:
            raise ValueError(
                "The CSV file does not contain any data."
            )

        return dataframe
