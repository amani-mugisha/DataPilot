from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from apps.exporter.writers.csv_writer import CSVWriter
from apps.exporter.writers.pdf_writer import PDFWriter


class ExportService:
    """
    Central export coordinator.

    The service selects the appropriate writer based on the requested
    output format and delegates the actual file generation to that writer.
    """

    def __init__(self) -> None:
        self.writers = {
            "csv": CSVWriter(),
            "pdf": PDFWriter(),
        }

    def supported_formats(self) -> list[str]:
        """Return the formats currently supported by DataPilot."""
        return sorted(self.writers.keys())

    def export(
        self,
        dataframe: pd.DataFrame,
        output_path: str | Path | BinaryIO,
        file_format: str,
        **kwargs,
    ):
        """
        Export a DataFrame using the writer registered for the format.

        Raises:
            ValueError: If the requested format is unsupported.
        """

        if not isinstance(file_format, str):
            raise ValueError("Export format must be a string.")

        normalized_format = file_format.strip().lower()

        if not normalized_format:
            raise ValueError("Export format cannot be empty.")

        writer = self.writers.get(normalized_format)

        if writer is None:
            supported = ", ".join(self.supported_formats())

            raise ValueError(
                f"Unsupported export format '{normalized_format}'. "
                f"Supported formats: {supported}"
            )

        return writer.write(
            dataframe,
            output_path,
            **kwargs,
        )
