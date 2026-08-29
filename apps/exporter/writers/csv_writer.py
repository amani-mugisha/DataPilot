from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base_writer import BaseWriter


class CSVWriter(BaseWriter):
    """
    Write a pandas DataFrame to CSV.

    The writer owns filesystem preparation and delegates CSV
    serialization to pandas.
    """

    format_name = "csv"

    def write(
        self,
        dataframe: pd.DataFrame,
        output_path: str | Path,
        **kwargs,
    ) -> Path:
        """
        Write a DataFrame to a CSV file.

        Args:
            dataframe:
                DataFrame to export.

            output_path:
                Destination CSV path.

            **kwargs:
                Additional pandas ``DataFrame.to_csv`` options.

        Returns:
            Path to the generated CSV file.
        """

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
            **kwargs,
        )

        return path
