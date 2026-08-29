from __future__ import annotations

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.datasets.models import Dataset
from apps.datasets.services import (
    DatasetLifecycleError,
    DatasetLifecycleService,
)


class DatasetLifecycleServiceTests(TestCase):

    def _create_dataset(
        self,
        status=Dataset.Status.UPLOADED,
    ):
        return Dataset.objects.create(
            name="Customers",
            original_file=SimpleUploadedFile(
                "customers.csv",
                b"name,age\nAmani,20\n",
                content_type="text/csv",
            ),
            status=status,
        )

    def test_uploaded_can_start_processing(self):
        dataset = self._create_dataset()

        DatasetLifecycleService.start_processing(
            dataset
        )

        dataset.refresh_from_db()

        self.assertEqual(
            dataset.status,
            Dataset.Status.PROCESSING,
        )

        self.assertIsNotNone(
            dataset.processing_started_at
        )

    def test_processing_can_return_to_uploaded(self):
        dataset = self._create_dataset(
            Dataset.Status.PROCESSING
        )

        DatasetLifecycleService.mark_uploaded(
            dataset
        )

        dataset.refresh_from_db()

        self.assertEqual(
            dataset.status,
            Dataset.Status.UPLOADED,
        )

        self.assertIsNotNone(
            dataset.completed_at
        )

    def test_processing_can_be_marked_cleaned(self):
        dataset = self._create_dataset(
            Dataset.Status.PROCESSING
        )

        DatasetLifecycleService.mark_cleaned(
            dataset
        )

        dataset.refresh_from_db()

        self.assertEqual(
            dataset.status,
            Dataset.Status.CLEANED,
        )

        self.assertIsNotNone(
            dataset.completed_at
        )

    def test_processing_can_fail(self):
        dataset = self._create_dataset(
            Dataset.Status.PROCESSING
        )

        DatasetLifecycleService.mark_failed(
            dataset,
            "Unable to analyze dataset.",
        )

        dataset.refresh_from_db()

        self.assertEqual(
            dataset.status,
            Dataset.Status.FAILED,
        )

        self.assertEqual(
            dataset.error_message,
            "Unable to analyze dataset.",
        )

    def test_failed_dataset_can_be_retried(self):
        dataset = self._create_dataset(
            Dataset.Status.FAILED
        )

        dataset.error_message = "Previous failure."
        dataset.save()

        DatasetLifecycleService.start_processing(
            dataset
        )

        dataset.refresh_from_db()

        self.assertEqual(
            dataset.status,
            Dataset.Status.PROCESSING,
        )

        self.assertEqual(
            dataset.error_message,
            "",
        )

    def test_cleaned_dataset_can_be_reprocessed(self):
        dataset = self._create_dataset(
            Dataset.Status.CLEANED
        )

        DatasetLifecycleService.start_processing(
            dataset
        )

        dataset.refresh_from_db()

        self.assertEqual(
            dataset.status,
            Dataset.Status.PROCESSING,
        )

    def test_invalid_transition_is_rejected(self):
        dataset = self._create_dataset()

        with self.assertRaises(
            DatasetLifecycleError
        ):
            DatasetLifecycleService.mark_cleaned(
                dataset
            )

    def test_failed_transition_requires_no_empty_message(self):
        dataset = self._create_dataset(
            Dataset.Status.PROCESSING
        )

        DatasetLifecycleService.mark_failed(
            dataset,
            "",
        )

        dataset.refresh_from_db()

        self.assertEqual(
            dataset.status,
            Dataset.Status.FAILED,
        )