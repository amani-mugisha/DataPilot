from __future__ import annotations

from io import BytesIO

import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.datasets.models import Dataset, DatasetColumn
from apps.datasets.services.analyzer import analyze_dataset


class DatasetAnalyzerTests(TestCase):

    def _create_dataset(
        self,
        filename: str = "customers.csv",
        content: bytes = (
            b"name,age,city\n"
            b"Amani,20,Kigali\n"
            b"John,25,Butare\n"
            b"Mary,,Kigali\n"
        ),
    ) -> Dataset:
        uploaded_file = SimpleUploadedFile(
            filename,
            content,
            content_type="text/csv",
        )

        return Dataset.objects.create(
            name=filename,
            original_file=uploaded_file,
        )

    def test_analyzes_dataframe(self):
        dataset = self._create_dataset()

        dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John", "Mary"],
                "age": [20, 25, None],
                "city": ["Kigali", "Butare", "Kigali"],
            }
        )

        result = analyze_dataset(
            dataset,
            dataframe,
        )

        result.refresh_from_db()

        self.assertEqual(
            result.row_count,
            3,
        )

        self.assertEqual(
            result.column_count,
            3,
        )

        self.assertEqual(
            result.status,
            Dataset.Status.UPLOADED,
        )

    def test_creates_dataset_columns(self):
        dataset = self._create_dataset()

        dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
                "city": ["Kigali", "Butare"],
            }
        )

        analyze_dataset(
            dataset,
            dataframe,
        )

        columns = DatasetColumn.objects.filter(
            dataset=dataset
        ).order_by("id")

        self.assertEqual(
            columns.count(),
            3,
        )

        self.assertEqual(
            list(columns.values_list("name", flat=True)),
            ["name", "age", "city"],
        )

    def test_records_column_data_types(self):
        dataset = self._create_dataset()

        dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

        analyze_dataset(
            dataset,
            dataframe,
        )

        name_column = DatasetColumn.objects.get(
            dataset=dataset,
            name="name",
        )

        age_column = DatasetColumn.objects.get(
            dataset=dataset,
            name="age",
        )

        self.assertEqual(
            name_column.data_type,
            str(dataframe["name"].dtype),
        )

        self.assertEqual(
            age_column.data_type,
            str(dataframe["age"].dtype),
        )

    def test_records_missing_values(self):
        dataset = self._create_dataset()

        dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John", None],
                "age": [20, None, 25],
            }
        )

        analyze_dataset(
            dataset,
            dataframe,
        )

        name_column = DatasetColumn.objects.get(
            dataset=dataset,
            name="name",
        )

        age_column = DatasetColumn.objects.get(
            dataset=dataset,
            name="age",
        )

        self.assertEqual(
            name_column.missing_count,
            1,
        )

        self.assertEqual(
            age_column.missing_count,
            1,
        )

    def test_records_unique_values(self):
        dataset = self._create_dataset()

        dataframe = pd.DataFrame(
            {
                "city": [
                    "Kigali",
                    "Kigali",
                    "Butare",
                    None,
                ],
            }
        )

        analyze_dataset(
            dataset,
            dataframe,
        )

        column = DatasetColumn.objects.get(
            dataset=dataset,
            name="city",
        )

        self.assertEqual(
            column.unique_count,
            2,
        )

    def test_replaces_existing_column_metadata(self):
        dataset = self._create_dataset()

        first_dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

        analyze_dataset(
            dataset,
            first_dataframe,
        )

        self.assertEqual(
            DatasetColumn.objects.filter(
                dataset=dataset
            ).count(),
            2,
        )

        second_dataframe = pd.DataFrame(
            {
                "customer": ["Amani", "John"],
                "city": ["Kigali", "Butare"],
                "active": [True, False],
            }
        )

        analyze_dataset(
            dataset,
            second_dataframe,
        )

        columns = DatasetColumn.objects.filter(
            dataset=dataset
        )

        self.assertEqual(
            columns.count(),
            3,
        )

        self.assertEqual(
            set(columns.values_list("name", flat=True)),
            {"customer", "city", "active"},
        )

    def test_sets_file_size(self):
        content = b"name,age\nAmani,20\n"

        dataset = self._create_dataset(
            content=content,
        )

        dataframe = pd.DataFrame(
            {
                "name": ["Amani"],
                "age": [20],
            }
        )

        analyze_dataset(
            dataset,
            dataframe,
        )

        dataset.refresh_from_db()

        self.assertEqual(
            dataset.file_size,
            len(content),
        )

    def test_loads_dataframe_through_importer_when_not_supplied(self):
        dataset = self._create_dataset()

        result = analyze_dataset(
            dataset
        )

        result.refresh_from_db()

        self.assertEqual(
            result.row_count,
            3,
        )

        self.assertEqual(
            result.column_count,
            3,
        )

        self.assertEqual(
            DatasetColumn.objects.filter(
                dataset=dataset
            ).count(),
            3,
        )

    def test_marks_dataset_failed_when_analysis_fails(self):
        dataset = self._create_dataset()

        invalid_dataframe = object()

        with self.assertRaises(
            Exception
        ):
            analyze_dataset(
                dataset,
                invalid_dataframe,
            )

        dataset.refresh_from_db()

        self.assertEqual(
            dataset.status,
            Dataset.Status.FAILED,
        )

    def test_sets_processing_started_at(self):
        dataset = self._create_dataset()

        dataframe = pd.DataFrame(
            {
                "name": ["Amani"],
            }
        )

        analyze_dataset(
            dataset,
            dataframe,
        )

        dataset.refresh_from_db()

        self.assertIsNotNone(
            dataset.processing_started_at,
        )

    def test_sets_completed_at_after_success(self):
        dataset = self._create_dataset()

        dataframe = pd.DataFrame(
            {
                "name": ["Amani"],
            }
        )

        analyze_dataset(
            dataset,
            dataframe,
        )

        dataset.refresh_from_db()

        self.assertIsNotNone(
            dataset.completed_at,
        )

    def test_clears_error_message_after_success(self):
        dataset = self._create_dataset()

        dataset.error_message = "Previous failure"
        dataset.save()

        dataframe = pd.DataFrame(
            {
                "name": ["Amani"],
            }
        )

        analyze_dataset(
            dataset,
            dataframe,
        )

        dataset.refresh_from_db()

        self.assertEqual(
            dataset.error_message,
            "",
        )

    def test_records_error_message_when_analysis_fails(self):
        dataset = self._create_dataset()

        invalid_dataframe = object()

        with self.assertRaises(TypeError):
            analyze_dataset(
                dataset,
                invalid_dataframe,
            )

        dataset.refresh_from_db()

        self.assertEqual(
            dataset.status,
            Dataset.Status.FAILED,
        )

        self.assertTrue(
            dataset.error_message,
        )