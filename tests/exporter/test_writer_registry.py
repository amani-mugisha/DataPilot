from __future__ import annotations

from django.test import SimpleTestCase

from apps.exporter.writers import (
    BaseWriter,
    CSVWriter,
    ExcelWriter,
    PDFWriter,
    WRITERS,
    get_writer,
)


class WriterRegistryTests(SimpleTestCase):

    def test_registry_contains_csv_writer(self):
        writer = get_writer("csv")

        self.assertIsInstance(
            writer,
            CSVWriter,
        )

    def test_registry_contains_pdf_writer(self):
        writer = get_writer("pdf")

        self.assertIsInstance(
            writer,
            PDFWriter,
        )

    def test_registry_contains_excel_writer(self):
        for file_format in (
            "xlsx",
            "xlsm",
            "xltx",
            "xltm",
        ):
            with self.subTest(file_format=file_format):
                writer = get_writer(file_format)

                self.assertIsInstance(
                    writer,
                    ExcelWriter,
                )

    def test_all_registered_writers_implement_base_writer(self):
        for file_format, writer in WRITERS.items():
            with self.subTest(file_format=file_format):
                self.assertIsInstance(
                    writer,
                    BaseWriter,
                )

    def test_all_registered_formats_are_expected(self):
        self.assertEqual(
            set(WRITERS),
            {
                "csv",
                "pdf",
                "xlsx",
                "xlsm",
                "xltx",
                "xltm",
            },
        )

    def test_unknown_format_is_rejected(self):
        with self.assertRaisesMessage(
            ValueError,
            "No writer registered for format: json",
        ):
            get_writer("json")