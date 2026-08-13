import pandas as pd

from django.db import transaction

from .models import Dataset, DatasetColumn


@transaction.atomic
def analyze_dataset(dataset):
    """
    Read the uploaded CSV and populate dataset metadata
    and DatasetColumn records.
    """

    dataset.status = Dataset.Status.PROCESSING
    dataset.save(update_fields=["status", "updated_at"])

    try:
        df = pd.read_csv(dataset.original_file.path)

        dataset.row_count = len(df)
        dataset.column_count = len(df.columns)
        dataset.file_size = dataset.original_file.size

        dataset.save(
            update_fields=[
                "row_count",
                "column_count",
                "file_size",
                "status",
                "updated_at",
            ]
        )

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
        dataset.save(update_fields=["status", "updated_at"])

        return dataset

    except Exception:
        dataset.status = Dataset.Status.FAILED
        dataset.save(update_fields=["status", "updated_at"])
        raise