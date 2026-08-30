from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from apps.exporter.formats import (
    SUPPORTED_EXPORT_FORMATS,
    normalize_export_format,
)
from apps.exporter.writers import (
    WRITERS,
    BaseWriter,
)


class ExportService:
    """
    Central export coordinator.

    Workflow:

        requested format
            ↓
        normalization
            ↓
        writer registry
            ↓
        format-specific writer
            ↓
        output file
    """

    def __init__(self) -> None:

        self.writers: dict[str, BaseWriter] = WRITERS

        self._validate_registry()

    # Registry
    def _validate_registry(self) -> None:
        """
        Validate exporter registry configuration.

        Every registered writer must:

            1. Implement BaseWriter.
            2. Declare a format_name.
            3. Represent a supported export format.
        """

        supported_formats = set(
            SUPPORTED_EXPORT_FORMATS
        )

        registered_formats = set(
            self.writers
        )

        unsupported_writers = (
            registered_formats - supported_formats
        )

        if unsupported_writers:
            formats = ", ".join(
                sorted(unsupported_writers)
            )

            raise RuntimeError(
                "Writer registered for unsupported "
                f"export format: {formats}"
            )

        for file_format, writer in self.writers.items():

            if not isinstance(
                writer,
                BaseWriter,
            ):
                raise RuntimeError(
                    f"Writer registered for '{file_format}' "
                    "does not implement BaseWriter."
                )

            if not writer.format_name:
                raise RuntimeError(
                    f"Writer registered for '{file_format}' "
                    "does not declare format_name."
                )

    # Metadata
    def supported_formats(self) -> list[str]:
        """
        Return all formats currently supported for export.
        """

        return sorted(
            self.writers.keys()
        )

    # Export
    def export(
        self,
        dataframe: pd.DataFrame,
        output_path: str | Path | BinaryIO,
        file_format: str,
        **kwargs,
    ):
        """
        Export a DataFrame using the registered writer.
        """

        writer = self.get_writer(
            file_format
        )

        return writer.write(
            dataframe,
            output_path,
            **kwargs,
        )

    # Writer lookup
    def get_writer(
        self,
        file_format: str,
    ) -> BaseWriter:
        """
        Return the writer registered for an export format.
        """

        normalized_format = normalize_export_format(
            file_format
        )

        writer = self.writers.get(
            normalized_format
        )

        if writer is None:
            supported = ", ".join(
                self.supported_formats()
            )

            raise ValueError(
                f"No writer registered for format "
                f"'{normalized_format}'. "
                f"Supported formats: {supported}"
            )

        return writer