from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from apps.importer.detectors.file_detector import (
    DetectedFile,
    detect_file,
)
from apps.importer.readers import BaseReader, CSVReader
from apps.importer.validators import (
    BaseValidator,
    CSVValidator,
)


class ImportService:
    """
    Central coordinator for DataPilot file importing.

    The service is responsible for orchestration only.

    Workflow:

        filename
            ↓
        File detection
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
        self.readers = self._build_readers()
        self.validators = self._build_validators()

        self._validate_registry()

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

    def _build_readers(self) -> dict[str, BaseReader]:
        """
        Build the reader registry.

        Additional formats can be registered here without changing
        the public ImportService interface.
        """

        return {
            "csv": CSVReader(),
        }

    def _build_validators(self) -> dict[str, BaseValidator]:
        """
        Build the validator registry.

        Additional format validators can be registered here later.
        """

        return {
            "csv": CSVValidator(),
        }

    def _validate_registry(self) -> None:
        """
        Ensure every registered reader has a corresponding validator.

        This prevents partially configured formats from silently
        reaching production.
        """

        reader_formats = set(self.readers)
        validator_formats = set(self.validators)

        missing_validators = (
            reader_formats - validator_formats
        )

        missing_readers = (
            validator_formats - reader_formats
        )

        if missing_validators:
            formats = ", ".join(
                sorted(missing_validators)
            )

            raise RuntimeError(
                "Missing validator registration for: "
                f"{formats}"
            )

        if missing_readers:
            formats = ", ".join(
                sorted(missing_readers)
            )

            raise RuntimeError(
                "Missing reader registration for: "
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
        """Detect the logical file format."""

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

        Returns:
            DetectedFile containing the detected file metadata.

        Raises:
            ValueError: If the format is unsupported or invalid.
        """

        detected = self.detect(
            filename or "",
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
            filename=filename,
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
    ) -> tuple[pd.DataFrame, DetectedFile]:
        """
        Validate, detect, and read an uploaded file.

        Returns:
            A tuple containing:

                - pandas DataFrame
                - DetectedFile metadata
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
            file_path
        )

        return dataframe, detected

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def supported_formats(self) -> list[str]:
        """Return formats currently supported by the importer."""

        return sorted(
            self.readers.keys()
        )
