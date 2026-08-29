from __future__ import annotations

from django.test import SimpleTestCase

from apps.importer.detectors import (
    SUPPORTED_FORMATS,
    detect_file,
)


class FileDetectorTests(SimpleTestCase):

    def test_supported_formats(self):
        self.assertEqual(
            SUPPORTED_FORMATS,
            {
                ".csv": "csv",

                ".xlsx": "excel_standard",
                ".xlsm": "excel_macro",
                ".xlsb": "excel_binary",

                ".xltx": "excel_template",
                ".xltm": "excel_template_macro",

                ".xlam": "excel_addin",
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

    def test_detects_xlsx(self):
        detected = detect_file(
            "customers.xlsx"
        )

        self.assertEqual(
            detected.extension,
            ".xlsx",
        )

        self.assertEqual(
            detected.format,
            "excel_standard",
        )

    def test_detects_xlsm(self):
        detected = detect_file(
            "customers.xlsm"
        )

        self.assertEqual(
            detected.extension,
            ".xlsm",
        )

        self.assertEqual(
            detected.format,
            "excel_macro",
        )

    def test_detects_xlsb(self):
        detected = detect_file(
            "customers.xlsb"
        )

        self.assertEqual(
            detected.extension,
            ".xlsb",
        )

        self.assertEqual(
            detected.format,
            "excel_binary",
        )

    def test_detects_xltx(self):
        detected = detect_file(
            "customers.xltx"
        )

        self.assertEqual(
            detected.extension,
            ".xltx",
        )

        self.assertEqual(
            detected.format,
            "excel_template",
        )

    def test_detects_xltm(self):
        detected = detect_file(
            "customers.xltm"
        )

        self.assertEqual(
            detected.extension,
            ".xltm",
        )

        self.assertEqual(
            detected.format,
            "excel_template_macro",
        )

    def test_detects_xlam(self):
        detected = detect_file(
            "customers.xlam"
        )

        self.assertEqual(
            detected.extension,
            ".xlam",
        )

        self.assertEqual(
            detected.format,
            "excel_addin",
        )

    def test_rejects_unknown_extension(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported file format: .txt",
        ):
            detect_file(
                "customers.txt"
            )

    def test_rejects_json(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported file format: .json",
        ):
            detect_file(
                "customers.json"
            )

    def test_rejects_filename_without_extension(self):
        with self.assertRaisesMessage(
            ValueError,
            "File has no extension.",
        ):
            detect_file(
                "customers"
            )