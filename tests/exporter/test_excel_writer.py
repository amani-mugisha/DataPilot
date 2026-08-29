from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import pandas as pd
from django.test import SimpleTestCase

from apps.exporter.writers import BaseWriter, ExcelWriter


class ExcelWriterTests(SimpleTestCase):

    def setUp(self):
        self.writer = ExcelWriter()

        self.dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

    def test_implements_base_writer(self):
        self.assertIsInstance(
            self.writer,
            BaseWriter,
        )

        self.assertEqual(
            self.writer.format_name,
            "excel",
        )

    def test_writes_xlsx(self):
        self._assert_excel_export(
            ".xlsx",
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet.main+xml",
        )

    def test_writes_xlsm(self):
        self._assert_excel_export(
            ".xlsm",
            "application/vnd.ms-excel.sheet.macroEnabled.main+xml",
        )

    def test_writes_xltx(self):
        self._assert_excel_export(
            ".xltx",
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.template.main+xml",
        )

    def test_writes_xltm(self):
        self._assert_excel_export(
            ".xltm",
            "application/vnd.ms-excel.template.macroEnabled.main+xml",
        )

    def test_creates_parent_directories(self):
        with TemporaryDirectory() as directory:
            path = (
                Path(directory)
                / "nested"
                / "deep"
                / "output.xlsx"
            )

            result = self.writer.write(
                self.dataframe,
                path,
            )

            self.assertEqual(
                result,
                path,
            )

            self.assertTrue(
                path.exists()
            )

    def test_rejects_none_dataframe(self):
        with self.assertRaisesMessage(
            ValueError,
            "ExcelWriter.write() requires a DataFrame.",
        ):
            self.writer.write(
                None,
                "/tmp/output.xlsx",
            )

    def test_rejects_missing_extension(self):
        with self.assertRaisesMessage(
            ValueError,
            "Excel output filename must have an extension.",
        ):
            self.writer.write(
                self.dataframe,
                "/tmp/output",
            )

    def test_rejects_non_exportable_excel_format(self):
        with self.assertRaisesMessage(
            ValueError,
            "Excel format .xlsb is not supported for export.",
        ):
            self.writer.write(
                self.dataframe,
                "/tmp/output.xlsb",
            )

    def test_supports_to_excel_options(self):
        with TemporaryDirectory() as directory:
            path = (
                Path(directory)
                / "output.xlsx"
            )

            self.writer.write(
                self.dataframe,
                path,
                sheet_name="Customers",
            )

            loaded = pd.read_excel(
                path,
                sheet_name="Customers",
                engine="openpyxl",
            )

            pd.testing.assert_frame_equal(
                loaded,
                self.dataframe,
            )

    def _assert_excel_export(
        self,
        extension: str,
        expected_content_type: str,
    ):
        with TemporaryDirectory() as directory:
            path = (
                Path(directory)
                / f"output{extension}"
            )

            result = self.writer.write(
                self.dataframe,
                path,
            )

            self.assertEqual(
                result,
                path,
            )

            self.assertTrue(
                path.exists()
            )

            self.assertGreater(
                path.stat().st_size,
                0,
            )

            with ZipFile(
                path,
                "r",
            ) as archive:

                self.assertIn(
                    "[Content_Types].xml",
                    archive.namelist(),
                )

                content_types = archive.read(
                    "[Content_Types].xml"
                ).decode(
                    "utf-8"
                )

            self.assertIn(
                expected_content_type,
                content_types,
            )

from pathlib import Path
from zipfile import ZipFile

import pandas as pd
from django.test import SimpleTestCase

from apps.exporter.writers import BaseWriter, ExcelWriter


class ExcelWriterTests(SimpleTestCase):

    def setUp(self):
        self.writer = ExcelWriter()

        self.dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def test_implements_base_writer(self):
        self.assertIsInstance(
            self.writer,
            BaseWriter,
        )

        self.assertEqual(
            self.writer.format_name,
            "excel",
        )

    # ------------------------------------------------------------------
    # Standard workbook
    # ------------------------------------------------------------------

    def test_writes_xlsx(self):
        self._assert_excel_export(
            ".xlsx",
            (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet.main+xml"
            ),
        )

    # ------------------------------------------------------------------
    # Macro-enabled workbook
    # ------------------------------------------------------------------

    def test_writes_xlsm(self):
        self._assert_excel_export(
            ".xlsm",
            "application/vnd.ms-excel.sheet.macroEnabled.main+xml",
        )

    # ------------------------------------------------------------------
    # Template
    # ------------------------------------------------------------------

    def test_writes_xltx(self):
        self._assert_excel_export(
            ".xltx",
            (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.template.main+xml"
            ),
        )

    # ------------------------------------------------------------------
    # Macro-enabled template
    # ------------------------------------------------------------------

    def test_writes_xltm(self):
        self._assert_excel_export(
            ".xltm",
            "application/vnd.ms-excel.template.macroEnabled.main+xml",
        )

    # ------------------------------------------------------------------
    # Nested directories
    # ------------------------------------------------------------------

    def test_creates_parent_directory(self):
        output_path = Path(
            "/tmp/datapilot-excel-tests/nested/output.xlsx"
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

        finally:
            output_path.unlink(
                missing_ok=True
            )

    # ------------------------------------------------------------------
    # DataFrame validation
    # ------------------------------------------------------------------

    def test_rejects_none_dataframe(self):
        with self.assertRaisesMessage(
            ValueError,
            "ExcelWriter.write() requires a DataFrame.",
        ):
            self.writer.write(
                None,
                "/tmp/output.xlsx",
            )

    # ------------------------------------------------------------------
    # Filename validation
    # ------------------------------------------------------------------

    def test_rejects_missing_extension(self):
        with self.assertRaisesMessage(
            ValueError,
            "Excel output filename must have an extension.",
        ):
            self.writer.write(
                self.dataframe,
                "/tmp/output",
            )

    def test_rejects_unsupported_excel_extension(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported Excel extension: .xls",
        ):
            self.writer.write(
                self.dataframe,
                "/tmp/output.xls",
            )

    # ------------------------------------------------------------------
    # Non-exportable formats
    # ------------------------------------------------------------------

    def test_rejects_xlsb(self):
        with self.assertRaisesMessage(
            ValueError,
            "Excel format .xlsb is not supported for export.",
        ):
            self.writer.write(
                self.dataframe,
                "/tmp/output.xlsb",
            )

    def test_rejects_xlam(self):
        with self.assertRaisesMessage(
            ValueError,
            "Excel format .xlam is not supported for export.",
        ):
            self.writer.write(
                self.dataframe,
                "/tmp/output.xlam",
            )

    # ------------------------------------------------------------------
    # Pandas options
    # ------------------------------------------------------------------

    def test_supports_to_excel_options(self):
        output_path = Path(
            "/tmp/datapilot-excel-options-test.xlsx"
        )

        try:
            self.writer.write(
                self.dataframe,
                output_path,
                sheet_name="Customers",
            )

            loaded = pd.read_excel(
                output_path,
                sheet_name="Customers",
                engine="openpyxl",
            )

            pd.testing.assert_frame_equal(
                loaded,
                self.dataframe,
            )

        finally:
            output_path.unlink(
                missing_ok=True
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _assert_excel_export(
        self,
        extension: str,
        expected_content_type: str,
    ):
        output_path = Path(
            f"/tmp/datapilot-excel-writer-test{extension}"
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

            self.assertGreater(
                output_path.stat().st_size,
                0,
            )

            with ZipFile(
                output_path,
                "r",
            ) as archive:

                content_types = archive.read(
                    "[Content_Types].xml"
                ).decode("utf-8")

            self.assertIn(
                expected_content_type,
                content_types,
            )

        finally:
            output_path.unlink(
                missing_ok=True
            )