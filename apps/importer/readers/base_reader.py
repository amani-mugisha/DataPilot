from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

import pandas as pd


class BaseReader(ABC):
    """Abstract interface for all DataPilot file readers."""

    @abstractmethod
    def read(
        self,
        file_path: str | Path | BinaryIO,
    ) -> pd.DataFrame:
        """Read a supported file into a DataFrame."""
        raise NotImplementedError
