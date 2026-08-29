from __future__ import annotations

from pathlib import Path

import pandas as pd
from django.test import SimpleTestCase

from apps.exporter.writers import (
    BaseWriter,
    CSVWriter,
    ExcelWriter,
    PDFWriter,
)


class WriterContractTests(SimpleTestCase):

    def test_csv_writer_implements_base_writer(self):
        writer = CSVWriter()

        self.assertIsInstance(
            writer,
            BaseWriter,
        )

        self.assertEqual(
            writer.format_name,
            "csv",
        )

    def test_pdf_writer_implements_base_writer(self):
        writer = PDFWriter()

        self.assertIsInstance(
            writer,
            BaseWriter,
        )

        self.assertEqual(
            writer.format_name,
            "pdf",
        )


class CSVWriterTests(SimpleTestCase):

    def setUp(self):
        self.writer = CSVWriter()

        self.dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

    def test_writes_csv(self):
        output_path = Path(
            "/tmp/datapilot-csv-writer-test.csv"
        )

        try:
            result = self.writer.write(
                self.dataframe,
                output_path,
            )

            self.assertEqual(
                result,
                output_path,
            )

            self.assertTrue(
                output_path.exists()
            )

            loaded = pd.read_csv(output_path)

            pd.testing.assert_frame_equal(
                loaded,
                self.dataframe,
            )

        finally:
            output_path.unlink(missing_ok=True)

    def test_creates_parent_directory(self):
        output_path = Path(
            "/tmp/datapilot-csv-writer-tests/nested/output.csv"
        )

        try:
            self.writer.write(
                self.dataframe,
                output_path,
            )

            self.assertTrue(
                output_path.exists()
            )

        finally:
            output_path.unlink(missing_ok=True)

    def test_rejects_none_dataframe(self):
        with self.assertRaisesMessage(
            ValueError,
            "CSVWriter.write() requires a DataFrame.",
        ):
            self.writer.write(
                None,
                "/tmp/output.csv",
            )


class PDFWriterTests(SimpleTestCase):

    def setUp(self):
        self.writer = PDFWriter()

        self.dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

    def test_writes_pdf(self):
        output_path = Path(
            "/tmp/datapilot-pdf-writer-test.pdf"
        )

        try:
            result = self.writer.write(
                self.dataframe,
                output_path,
                original_filename="customers.csv",
            )

            self.assertEqual(
                result,
                output_path,
            )

            self.assertTrue(
                output_path.exists()
            )

            self.assertGreater(
                output_path.stat().st_size,
                0,
            )

            with output_path.open(
                "rb"
            ) as file:
                header = file.read(5)

            self.assertEqual(
                header,
                b"%PDF-",
            )

        finally:
            output_path.unlink(missing_ok=True)

    def test_writes_empty_dataframe(self):
        dataframe = pd.DataFrame(
            columns=["name", "age"]
        )

        output_path = Path(
            "/tmp/datapilot-empty-pdf-test.pdf"
        )

        try:
            self.writer.write(
                dataframe,
                output_path,
            )

            self.assertTrue(
                output_path.exists()
            )

            self.assertGreater(
                output_path.stat().st_size,
                0,
            )

        finally:
            output_path.unlink(missing_ok=True)

    def test_rejects_none_dataframe(self):
        with self.assertRaisesMessage(
            ValueError,
            "PDFWriter.write() requires a DataFrame.",
        ):
            self.writer.write(
                None,
                "/tmp/output.pdf",
            )