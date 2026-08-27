from __future__ import annotations

from django.test import SimpleTestCase

from apps.importer.detectors import (
    SUPPORTED_FORMATS,
    detect_file,
)


class FileDetectorTests(SimpleTestCase):

    def test_supported_formats_contains_csv_only(self):
        self.assertEqual(
            SUPPORTED_FORMATS,
            {
                ".csv": "csv",
            },
        )

    def test_detects_csv(self):
        detected = detect_file(
            "customers.csv"
        )

        self.assertEqual(
            detected.filename,
            "customers.csv",
        )

        self.assertEqual(
            detected.extension,
            ".csv",
        )

        self.assertEqual(
            detected.format,
            "csv",
        )

    def test_detects_uppercase_csv(self):
        detected = detect_file(
            "CUSTOMERS.CSV"
        )

        self.assertEqual(
            detected.extension,
            ".csv",
        )

        self.assertEqual(
            detected.format,
            "csv",
        )

    def test_rejects_xlsx(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported file format: .xlsx",
        ):
            detect_file("customers.xlsx")

    def test_rejects_json(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported file format: .json",
        ):
            detect_file("customers.json")

    def test_rejects_unknown_extension(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported file format: .txt",
        ):
            detect_file("customers.txt")

    def test_rejects_filename_without_extension(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported file format: unknown",
        ):
            detect_file("customers")