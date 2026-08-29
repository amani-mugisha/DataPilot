from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from .base_validator import BaseValidator
from ..formats import SUPPORTED_FORMATS


class CSVValidationError(ValueError):
    """Raised when a CSV file fails validation."""


class CSVValidator(BaseValidator):
    """Validate CSV files before reading."""

    format_name = "csv"

    MAX_FILE_SIZE = 50 * 1024 * 1024

    def validate_filename(
        self,
        filename: str,
    ) -> None:
        """
        Validate that the supplied filename is a CSV filename.
        """

        if not filename:
            raise CSVValidationError(
                "CSV filename cannot be empty."
            )

        extension = Path(filename).suffix.lower()

        if extension != ".csv":
            raise CSVValidationError(
                "Only CSV files are supported."
            )

    def validate_size(
        self,
        file_size: int,
    ) -> None:
        """
        Validate CSV file size.
        """

        if file_size < 0:
            raise CSVValidationError(
                "CSV file size cannot be negative."
            )

        if file_size > self.MAX_FILE_SIZE:
            raise CSVValidationError(
                "The maximum CSV file size is 50MB."
            )

    def validate(
        self,
        file_path: str | Path | BinaryIO,
        filename: str | None = None,
        file_size: int | None = None,
    ) -> None:
        """
        Validate a CSV file.
        """

        if file_path is None:
            raise CSVValidationError(
                "CSVValidator.validate() requires a file."
            )

        name = filename or self._get_filename(file_path)

        self.validate_filename(name)

        if file_size is not None:
            self.validate_size(file_size)

        self._validate_content(file_path)

    def _validate_content(
        self,
        file_path: str | Path | BinaryIO,
    ) -> None:
        """
        Ensure the CSV contains data.
        """

        try:
            if isinstance(file_path, (str, Path)):

                path = Path(file_path)

                if not path.exists():
                    raise CSVValidationError(
                        "The CSV file does not exist."
                    )

                if path.stat().st_size == 0:
                    raise CSVValidationError(
                        "The CSV file is empty."
                    )

                with open(path, "rb") as file:
                    sample = file.read(4096)

            else:
                current_position = file_path.tell()

                sample = file_path.read(4096)

                file_path.seek(current_position)

            if not sample.strip():
                raise CSVValidationError(
                    "The CSV file is empty."
                )

        except CSVValidationError:
            raise

        except FileNotFoundError as exc:
            raise CSVValidationError(
                "The CSV file does not exist."
            ) from exc

        except Exception as exc:
            raise CSVValidationError(
                f"Unable to read CSV file: {exc}"
            ) from exc

    @staticmethod
    def _get_filename(
        file_path: str | Path | BinaryIO,
    ) -> str:

        if isinstance(file_path, (str, Path)):
            return Path(file_path).name

        name = getattr(file_path, "name", None)

        if name:
            return Path(name).name

        raise CSVValidationError(
            "filename is required for file-like objects."
        )