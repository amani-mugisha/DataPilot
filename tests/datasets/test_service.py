from __future__ import annotations

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.datasets.models import Dataset
from apps.datasets.services import DatasetService


class DatasetServiceTests(TestCase):

    def setUp(self):
        self.service = DatasetService()

    def _file(
        self,
        name: str = "customers.csv",
        content: bytes = (
            b"name,age\n"
            b"Amani,20\n"
            b"John,25\n"
        ),
    ):
        return SimpleUploadedFile(
            name,
            content,
            content_type="text/csv",
        )

    def test_creates_dataset(self):
        dataset = self.service.create(
            name="Customers",
            uploaded_file=self._file(),
        )

        self.assertIsNotNone(
            dataset.pk
        )

        self.assertEqual(
            dataset.name,
            "Customers",
        )

        self.assertEqual(
            dataset.status,
            Dataset.Status.UPLOADED,
        )

    def test_stores_original_filename(self):
        dataset = self.service.create(
            name="Customers",
            uploaded_file=self._file(
                name="customers.csv"
            ),
        )

        self.assertEqual(
            dataset.original_filename,
            "customers.csv",
        )

    def test_detects_file_type(self):
        dataset = self.service.create(
            name="Customers",
            uploaded_file=self._file(),
        )

        self.assertEqual(
            dataset.file_type,
            "csv",
        )

    def test_stores_mime_type(self):
        dataset = self.service.create(
            name="Customers",
            uploaded_file=self._file(),
        )

        self.assertEqual(
            dataset.mime_type,
            "text/csv",
        )

    def test_stores_file_size(self):
        content = (
            b"name,age\n"
            b"Amani,20\n"
        )

        dataset = self.service.create(
            name="Customers",
            uploaded_file=self._file(
                content=content
            ),
        )

        self.assertEqual(
            dataset.file_size,
            len(content),
        )

    def test_calculates_sha256_checksum(self):
        dataset = self.service.create(
            name="Customers",
            uploaded_file=self._file(),
        )

        self.assertEqual(
            len(dataset.checksum),
            64,
        )

        self.assertTrue(
            all(
                character in "0123456789abcdef"
                for character in dataset.checksum
            )
        )

    def test_rejects_empty_name(self):
        with self.assertRaisesMessage(
            ValueError,
            "Dataset name cannot be empty.",
        ):
            self.service.create(
                name="   ",
                uploaded_file=self._file(),
            )

    def test_rejects_missing_file(self):
        with self.assertRaisesMessage(
            ValueError,
            "Dataset file is required.",
        ):
            self.service.create(
                name="Customers",
                uploaded_file=None,
            )

    def test_rejects_unsupported_file(self):
        unsupported = SimpleUploadedFile(
            "customers.json",
            b'{"name": "Amani"}',
            content_type="application/json",
        )

        with self.assertRaises(ValueError):
            self.service.create(
                name="Customers",
                uploaded_file=unsupported,
            )

        self.assertEqual(
            Dataset.objects.count(),
            0,
        )

    def test_preserves_uploaded_file_position(self):
        uploaded_file = self._file()

        uploaded_file.seek(3)

        self.service.create(
            name="Customers",
            uploaded_file=uploaded_file,
        )

        self.assertEqual(
            uploaded_file.tell(),
            0,
        )

    def test_validate_file_does_not_create_dataset(self):
        result = self.service.validate_file(
            self._file()
        )

        self.assertEqual(
            result.format,
            "csv",
        )

        self.assertEqual(
            Dataset.objects.count(),
            0,
        )
