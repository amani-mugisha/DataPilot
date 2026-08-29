from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from .detectors import detect_format
from .readers.registry import get_reader
from .validators.registry import get_validator


class ImporterService:
    """
    Main orchestration service for DataPilot file imports.

    Flow:

        detect → validate → read → DataFrame
    """

    def import_file(
        self,
        file_path: str | Path | BinaryIO,
        filename: str | None = None,
        file_size: int | None = None,
    ) -> pd.DataFrame:

        name = filename or self._get_filename(file_path)

        # --------------------------------------------------
        # 1. Detect format
        # --------------------------------------------------

        format_type = detect_format(name)

        # --------------------------------------------------
        # 2. Get validator
        # --------------------------------------------------

        validator = get_validator(format_type)

        # --------------------------------------------------
        # 3. Validate
        # --------------------------------------------------

        validator.validate(
            file_path=file_path,
            filename=name,
            file_size=file_size,
        )

        # --------------------------------------------------
        # 4. Get reader
        # --------------------------------------------------

        reader = get_reader(format_type)

        # --------------------------------------------------
        # 5. Read into DataFrame
        # --------------------------------------------------

        return reader.read(file_path)

    @staticmethod
    def _get_filename(
        file_path: str | Path | BinaryIO,
    ) -> str:

        if isinstance(file_path, (str, Path)):
            return Path(file_path).name

        raise ValueError(
            "filename is required when importing a file-like object."
        )