from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

import pandas as pd


class BaseReader(ABC):
    """
    Abstract contract for all DataPilot file readers.

    Every reader must expose the same public interface so that
    ImportService never needs to know format-specific details.
    """

    format_name: str

    @abstractmethod
    def read(
        self,
        file_path: str | Path | BinaryIO,
        *,
        filename: str | None = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Read a file into a pandas DataFrame.

        Args:
            file_path:
                Filesystem path or file-like object.

            filename:
                Original filename when file_path is file-like.

            **kwargs:
                Format-specific reader options.

        Returns:
            pandas.DataFrame

        Raises:
            ValueError:
                If the file cannot be read.
        """
        raise NotImplementedError