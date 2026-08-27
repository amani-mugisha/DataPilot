from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class BaseWriter(ABC):
    """
    Abstract base class for all DataPilot exporters.

    Every writer must:
        - declare its format_name
        - implement write()
    """

    format_name: str

    @abstractmethod
    def write(
        self,
        dataframe: pd.DataFrame,
        output_path: str | Path,
        **kwargs,
    ) -> Path:
        """
        Write a DataFrame to the target format.

        Args:
            dataframe: DataFrame to export.
            output_path: Destination path.
            **kwargs: Format-specific options.

        Returns:
            Path to the generated file.
        """
        raise NotImplementedError
