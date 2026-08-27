from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base_writer import BaseWriter


class CSVWriter(BaseWriter):
    """Write a pandas DataFrame to CSV."""

    format_name = "csv"

    def write(
        self,
        dataframe: pd.DataFrame,
        output_path: str | Path,
        **kwargs,
    ) -> Path:

        if dataframe is None:
            raise ValueError(
                "CSVWriter.write() requires a DataFrame."
            )

        path = Path(output_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        dataframe.to_csv(
            path,
            index=False,
        )

        return path
