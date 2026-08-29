from __future__ import annotations

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase

from apps.datasets.models import Dataset, DatasetColumn


class DatasetModelTests(TestCase):

    def _create_dataset(self) -> Dataset:
        return Dataset.objects.create(
            name="Customers",
            original_file=SimpleUploadedFile(
                "customers.csv",
                b"name,age\nAmani,20\n",
                content_type="text/csv",
            ),
        )

    def test_dataset_defaults_are_correct(self):
        dataset = self._create_dataset()

        self.assertEqual(
            dataset.status,
            Dataset.Status.UPLOADED,
        )

        self.assertEqual(
            dataset.file_size,
            0,
        )

        self.assertEqual(
            dataset.row_count,
            0,
        )

        self.assertEqual(
            dataset.column_count,
            0,
        )

    def test_dataset_columns_have_position(self):
        dataset = self._create_dataset()

        column = DatasetColumn.objects.create(
            dataset=dataset,
            name="name",
            data_type="object",
            position=0,
        )

        self.assertEqual(
            column.position,
            0,
        )

    def test_dataset_column_name_is_unique_per_dataset(self):
        dataset = self._create_dataset()

        DatasetColumn.objects.create(
            dataset=dataset,
            name="name",
        )

        with self.assertRaises(IntegrityError):
            DatasetColumn.objects.create(
                dataset=dataset,
                name="name",
            )

    def test_same_column_name_allowed_on_different_datasets(self):
        first = self._create_dataset()

        second = Dataset.objects.create(
            name="Orders",
            original_file=SimpleUploadedFile(
                "orders.csv",
                b"id,total\n1,100\n",
                content_type="text/csv",
            ),
        )

        DatasetColumn.objects.create(
            dataset=first,
            name="id",
        )

        DatasetColumn.objects.create(
            dataset=second,
            name="id",
        )

        self.assertEqual(
            DatasetColumn.objects.filter(
                name="id"
            ).count(),
            2,
        )

    def test_deleting_dataset_deletes_columns(self):
        dataset = self._create_dataset()

        DatasetColumn.objects.create(
            dataset=dataset,
            name="name",
        )

        dataset.delete()

        self.assertEqual(
            DatasetColumn.objects.count(),
            0,
        )

    def test_dataset_error_message_defaults_to_empty(self):
        dataset = self._create_dataset()

        self.assertEqual(
            dataset.error_message,
            "",
        )

    def test_dataset_processing_started_at_defaults_to_none(self):
        dataset = self._create_dataset()

        self.assertIsNone(
            dataset.processing_started_at,
        )

    def test_dataset_completed_at_defaults_to_none(self):
        dataset = self._create_dataset()

        self.assertIsNone(
            dataset.completed_at,
        )

    def test_dataset_file_type_can_be_indexed(self):
        dataset = self._create_dataset()

        dataset.file_type = "csv"
        dataset.save()

        self.assertEqual(
            Dataset.objects.filter(
                file_type="csv"
            ).count(),
            1,
        )