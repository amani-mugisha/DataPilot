from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ImportResult:
    """
    Represents a completed DataPilot import operation.
    """

    filename: str
    extension: str
    format: str
    dataframe: pd.DataFrame
    mime_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        return len(self.dataframe.index)

    @property
    def column_count(self) -> int:
        return len(self.dataframe.columns)

    @property
    def shape(self) -> tuple[int, int]:
        return self.dataframe.shape

    def __iter__(self):
        """
        Preserve compatibility with the previous:

            dataframe, detected = service.read(...)
        """
        yield self.dataframe
        yield self