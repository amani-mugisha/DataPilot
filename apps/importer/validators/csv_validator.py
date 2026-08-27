from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from .base_validator import BaseValidator


class CSVValidator(BaseValidator):
    """
    Validate CSV files before they reach the CSV reader.

    Responsibilities:
        - Validate file existence.
        - Validate filename.
        - Validate file size.
        - Reject empty files.

    CSV parsing remains the responsibility of CSVReader.
    """

    format_name = "csv"

    MAX_FILE_SIZE = 50 * 1024 * 1024

    def validate(
        self,
        file_path: str | Path | BinaryIO,
        filename: str | None = None,
        file_size: int | None = None,
    ) -> None:
        """
        Validate a CSV file before reading.

        Raises:
            ValueError: If the file is invalid.
        """

        if file_path is None:
            raise ValueError(
                "CSVValidator.validate() requires a file."
            )

        if filename is not None:
            self.validate_filename(filename)

        if file_size is not None:
            self.validate_size(file_size)

        if isinstance(file_path, (str, Path)):
            path = Path(file_path)

            if not path.exists():
                raise ValueError(
                    "The CSV file does not exist."
                )

            if not path.is_file():
                raise ValueError(
                    "The CSV path is not a file."
                )

            if path.stat().st_size == 0:
                raise ValueError(
                    "The CSV file is empty."
                )

    def validate_filename(
        self,
        filename: str,
    ) -> None:
        """Validate a CSV filename."""

        if not filename or not filename.strip():
            raise ValueError(
                "CSV filename cannot be empty."
            )

        if not filename.lower().endswith(".csv"):
            raise ValueError(
                "Only CSV files are supported."
            )

    def validate_size(
        self,
        file_size: int,
    ) -> None:
        """Validate the CSV file size."""

        if file_size < 0:
            raise ValueError(
                "CSV file size cannot be negative."
            )

        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                "The maximum CSV file size is 50MB."
            )
