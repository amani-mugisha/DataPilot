from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from apps.importer.detectors.file_detector import (
    DetectedFile,
    detect_file,
)
from apps.importer.formats import SUPPORTED_FORMATS
from apps.importer.readers import BaseReader
from apps.importer.readers.registry import READERS
from apps.importer.validators import BaseValidator
from apps.importer.validators.registry import VALIDATORS
from apps.importer.results import ImportResult


class ImportService:
    """
    Central coordinator for DataPilot file importing.

    Workflow:

        filename
            ↓
        Detection
            ↓
        Validation
            ↓
        Reader selection
            ↓
        DataFrame

    Format-specific parsing and validation remain inside their
    respective reader and validator classes.
    """

    def __init__(self) -> None:
        self.readers: dict[str, BaseReader] = READERS
        self.validators: dict[str, BaseValidator] = VALIDATORS

        self._validate_registry()

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

    def _validate_registry(self) -> None:
        """
        Validate importer registry configuration.

        Registry rules:

        1. Every supported format must have a validator.
        2. Every registered reader must have a validator.
        3. Every registered reader must represent a supported format.
        4. Every registered validator must represent a supported format.

        A format may have a validator without having a reader.
        This supports validation-only formats such as Excel add-ins.
        """

        supported_formats = set(
            SUPPORTED_FORMATS.values()
        )

        reader_formats = set(
            self.readers
        )

        validator_formats = set(
            self.validators
        )

        # --------------------------------------------------------------
        # Supported formats must have validators
        # --------------------------------------------------------------

        missing_validators = (
            supported_formats - validator_formats
        )

        if missing_validators:
            formats = ", ".join(
                sorted(missing_validators)
            )

            raise RuntimeError(
                "Missing validator registration for: "
                f"{formats}"
            )

        # --------------------------------------------------------------
        # Readers must have validators
        # --------------------------------------------------------------

        readers_without_validators = (
            reader_formats - validator_formats
        )

        if readers_without_validators:
            formats = ", ".join(
                sorted(readers_without_validators)
            )

            raise RuntimeError(
                "Reader registered without validator for: "
                f"{formats}"
            )

        # --------------------------------------------------------------
        # Readers must represent supported formats
        # --------------------------------------------------------------

        unsupported_readers = (
            reader_formats - supported_formats
        )

        if unsupported_readers:
            formats = ", ".join(
                sorted(unsupported_readers)
            )

            raise RuntimeError(
                "Reader registered for unsupported format: "
                f"{formats}"
            )

        # --------------------------------------------------------------
        # Validators must represent supported formats
        # --------------------------------------------------------------

        unsupported_validators = (
            validator_formats - supported_formats
        )

        if unsupported_validators:
            formats = ", ".join(
                sorted(unsupported_validators)
            )

            raise RuntimeError(
                "Validator registered for unsupported format: "
                f"{formats}"
            )

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def detect(
        self,
        filename: str,
        mime_type: str | None = None,
    ) -> DetectedFile:
        """
        Detect the logical DataPilot format from a filename.
        """

        return detect_file(
            filename,
            mime_type,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(
        self,
        file_path: str | Path | BinaryIO,
        filename: str | None = None,
        file_size: int | None = None,
        mime_type: str | None = None,
    ) -> DetectedFile:
        """
        Detect and validate an uploaded file.
        """

        name = (
            filename
            if filename is not None
            else self._get_filename(file_path)
        )

        detected = self.detect(
            name,
            mime_type,
        )

        validator = self.validators.get(
            detected.format
        )

        if validator is None:
            raise ValueError(
                f"No validator is registered for "
                f"'{detected.format}'."
            )

        validator.validate(
            file_path=file_path,
            filename=name,
            file_size=file_size,
        )

        return detected

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def read(
        self,
        file_path: str | Path | BinaryIO,
        filename: str,
        mime_type: str | None = None,
        file_size: int | None = None,
        **reader_options,
    ) -> ImportResult:
        """
        Validate, detect, and read an uploaded file.

        Reader-specific options are passed through without the
        ImportService needing to know the file format.
        """

        detected = self.validate(
            file_path=file_path,
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
        )

        reader = self.readers.get(
            detected.format
        )

        if reader is None:
            raise ValueError(
                f"No reader is registered for "
                f"'{detected.format}'."
            )

        dataframe = reader.read(
            file_path,
            filename=detected.filename,
            **reader_options,
        )

        return ImportResult(
            filename=detected.filename,
            extension=detected.extension,
            format=detected.format,
            mime_type=detected.mime_type,
            dataframe=dataframe,
        )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def supported_formats(self) -> list[str]:
        """
        Return formats that can actually be imported
        into pandas DataFrames.
        """

        return sorted(
            self.readers.keys()
        )

    # ------------------------------------------------------------------
    # Excel
    # ------------------------------------------------------------------

    def list_sheets(
        self,
        file_path: str | Path | BinaryIO,
        filename: str,
    ) -> list[str]:
        """
        Return worksheet names for an Excel workbook.
        """

        detected = self.detect(
            filename
        )

        if not detected.format.startswith("excel_"):
            raise ValueError(
                "Sheet listing is only supported for Excel files."
            )

        reader = self.readers.get(
            detected.format
        )

        if reader is None:
            raise ValueError(
                f"No reader is registered for "
                f"'{detected.format}'."
            )

        if not hasattr(reader, "list_sheets"):
            raise ValueError(
                f"Reader for '{detected.format}' "
                "does not support sheet listing."
            )

        return reader.list_sheets(
            file_path,
            filename=filename,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_filename(
        file_path: str | Path | BinaryIO,
    ) -> str:
        """
        Extract filename from a filesystem path.

        File-like objects require the caller to provide filename.
        """

        if isinstance(
            file_path,
            (str, Path),
        ):
            return Path(file_path).name

        raise ValueError(
            "filename is required when importing "
            "a file-like object."
        )
