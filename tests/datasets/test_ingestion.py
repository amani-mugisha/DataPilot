from __future__ import annotations

from unittest.mock import patch

import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.cleaner.models import CleaningJob
from apps.datasets.models import Dataset, DatasetColumn
from apps.datasets.services import DatasetIngestionService


class DatasetIngestionServiceTests(TestCase):

    def setUp(self):
        self.service = DatasetIngestionService()

    def _file(
        self,
        name: str = "customers.csv",
        content: bytes = (
            b"name,age,city\n"
            b"Amani,20,Kigali\n"
            b"John,25,Butare\n"
            b"Mary,,Kigali\n"
        ),
    ):
        return SimpleUploadedFile(
            name,
            content,
            content_type="text/csv",
        )

    def test_ingests_dataset_successfully(self):
        result = self.service.ingest(
            name="Customers",
            uploaded_file=self._file(),
        )

        self.assertIsNotNone(
            result.dataset.pk,
        )

        self.assertIsNotNone(
            result.cleaning_job.pk,
        )

        self.assertEqual(
            result.dataset.name,
            "Customers",
        )

        self.assertEqual(
            result.dataset.status,
            Dataset.Status.UPLOADED,
        )

    def test_import_result_contains_dataframe(self):
        result = self.service.ingest(
            name="Customers",
            uploaded_file=self._file(),
        )

        self.assertIsInstance(
            result.import_result.dataframe,
            pd.DataFrame,
        )

        self.assertEqual(
            len(result.import_result.dataframe),
            3,
        )

    def test_analyzes_dataset(self):
        result = self.service.ingest(
            name="Customers",
            uploaded_file=self._file(),
        )

        dataset = result.dataset

        dataset.refresh_from_db()

        self.assertEqual(
            dataset.row_count,
            3,
        )

        self.assertEqual(
            dataset.column_count,
            3,
        )

        self.assertEqual(
            DatasetColumn.objects.filter(
                dataset=dataset,
            ).count(),
            3,
        )

    def test_creates_pending_cleaning_job(self):
        result = self.service.ingest(
            name="Customers",
            uploaded_file=self._file(),
        )

        job = result.cleaning_job

        self.assertEqual(
            job.dataset_id,
            result.dataset.id,
        )

        self.assertEqual(
            job.status,
            CleaningJob.Status.PENDING,
        )

        self.assertEqual(
            job.row_count,
            3,
        )

    def test_dataset_metadata_is_persisted(self):
        result = self.service.ingest(
            name="Customers",
            uploaded_file=self._file(),
        )

        dataset = result.dataset

        self.assertEqual(
            dataset.original_filename,
            "customers.csv",
        )

        self.assertEqual(
            dataset.file_type,
            "csv",
        )

        self.assertEqual(
            dataset.mime_type,
            "text/csv",
        )

        self.assertGreater(
            dataset.file_size,
            0,
        )

        self.assertEqual(
            len(dataset.checksum),
            64,
        )

    def test_rejects_missing_file(self):
        with self.assertRaisesMessage(
            ValueError,
            "Dataset file is required.",
        ):
            self.service.ingest(
                name="Customers",
                uploaded_file=None,
            )

        self.assertEqual(
            Dataset.objects.count(),
            0,
        )

        self.assertEqual(
            CleaningJob.objects.count(),
            0,
        )

    def test_rejects_unsupported_file(self):
        uploaded_file = SimpleUploadedFile(
            "customers.json",
            b'{"name": "Amani"}',
            content_type="application/json",
        )

        with self.assertRaises(ValueError):
            self.service.ingest(
                name="Customers",
                uploaded_file=uploaded_file,
            )

        self.assertEqual(
            Dataset.objects.count(),
            0,
        )

        self.assertEqual(
            CleaningJob.objects.count(),
            0,
        )

    def test_analysis_failure_marks_dataset_failed(self):
        with patch(
            "apps.datasets.services.ingestion.analyze_dataset",
            side_effect=RuntimeError(
                "Analysis failed."
            ),
        ):
            with self.assertRaisesMessage(
                RuntimeError,
                "Analysis failed.",
            ):
                self.service.ingest(
                    name="Customers",
                    uploaded_file=self._file(),
                )

        dataset = Dataset.objects.get()

        self.assertEqual(
            dataset.status,
            Dataset.Status.FAILED,
        )

        self.assertEqual(
            dataset.error_message,
            "Analysis failed.",
        )

        self.assertEqual(
            CleaningJob.objects.count(),
            0,
        )
