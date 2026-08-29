from __future__ import annotations

import pandas as pd
from django.db import transaction

from apps.datasets.models import Dataset, DatasetColumn
from apps.datasets.services.lifecycle import DatasetLifecycleService
from apps.importer.services import ImportService


def analyze_dataset(
    dataset: Dataset,
    df: pd.DataFrame | None = None,
) -> Dataset:
    """
    Analyze a dataset and persist structural metadata.

    Responsibilities:

        - load the dataframe when necessary
        - calculate dataset-level metadata
        - persist column-level metadata
        - delegate lifecycle state changes to
          DatasetLifecycleService

    Lifecycle:

        current state
            ↓
        PROCESSING
            ↓
        UPLOADED

    On failure:

        PROCESSING
            ↓
        FAILED
    """

    DatasetLifecycleService.start_processing(dataset)

    try:
        with transaction.atomic():

            if df is None:
                if not dataset.original_file:
                    raise ValueError(
                        "Dataset does not have an original file."
                    )

                importer = ImportService()

                result = importer.read(
                    file_path=dataset.original_file.path,
                    filename=dataset.original_file.name,
                )

                df = result.dataframe

            if not isinstance(df, pd.DataFrame):
                raise TypeError(
                    "Dataset analysis requires a pandas DataFrame."
                )

            # ---------------------------------------------------------
            # Dataset-level metadata
            # ---------------------------------------------------------

            dataset.row_count = len(df)
            dataset.column_count = len(df.columns)

            if dataset.original_file:
                dataset.file_size = dataset.original_file.size

                if not dataset.original_filename:
                    dataset.original_filename = (
                        dataset.original_file.name.rsplit(
                            "/",
                            1,
                        )[-1]
                    )

            dataset.save(
                update_fields=[
                    "row_count",
                    "column_count",
                    "file_size",
                    "original_filename",
                    "updated_at",
                ]
            )

            # ---------------------------------------------------------
            # Column-level metadata
            # ---------------------------------------------------------

            DatasetColumn.objects.filter(
                dataset=dataset,
            ).delete()

            columns = []

            for position, column in enumerate(df.columns):
                series = df[column]

                columns.append(
                    DatasetColumn(
                        dataset=dataset,
                        name=str(column),
                        data_type=str(series.dtype),
                        missing_count=int(
                            series.isna().sum()
                        ),
                        unique_count=int(
                            series.nunique(
                                dropna=True,
                            )
                        ),
                        position=position,
                    )
                )

            DatasetColumn.objects.bulk_create(
                columns
            )

            # ---------------------------------------------------------
            # Lifecycle completion
            # ---------------------------------------------------------

            DatasetLifecycleService.mark_uploaded(
                dataset
            )

    except Exception as exc:
        DatasetLifecycleService.mark_failed(
            dataset,
            str(exc),
        )
        raise

    return dataset