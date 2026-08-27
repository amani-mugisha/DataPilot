from __future__ import annotations

import pandas as pd
from django.db import transaction

from apps.datasets.models import Dataset, DatasetColumn

from apps.importer.services import ImportService


@transaction.atomic
def analyze_dataset(dataset: Dataset, df: pd.DataFrame | None = None) -> Dataset:
    """
    Analyze a dataset and populate dataset metadata and column information.

    If a DataFrame is supplied, it is analyzed directly.
    Otherwise the method currently falls back to reading the dataset file
    as CSV. The fallback will be removed when all file formats use the
    importer pipeline.
    """

    dataset.status = Dataset.Status.PROCESSING
    dataset.save(update_fields=["status", "updated_at"])

    try:
        if df is None:
            if not dataset.original_file:
                raise ValueError(
                    "Dataset does not have an original file."
                )

            importer = ImportService()

            df, _detected = importer.read(
                file_path=dataset.original_file.path,
                filename=dataset.original_file.name,
            )

        dataset.row_count = len(df)
        dataset.column_count = len(df.columns)
        dataset.file_size = dataset.original_file.size

        DatasetColumn.objects.filter(dataset=dataset).delete()

        columns = []

        for column in df.columns:
            series = df[column]

            columns.append(
                DatasetColumn(
                    dataset=dataset,
                    name=str(column),
                    data_type=str(series.dtype),
                    missing_count=int(series.isna().sum()),
                    unique_count=int(series.nunique(dropna=True)),
                )
            )

        DatasetColumn.objects.bulk_create(columns)

        dataset.status = Dataset.Status.UPLOADED
        dataset.save(
            update_fields=[
                "row_count",
                "column_count",
                "file_size",
                "status",
                "updated_at",
            ]
        )

        return dataset

    except Exception:
        dataset.status = Dataset.Status.FAILED
        dataset.save(update_fields=["status", "updated_at"])
        raise
