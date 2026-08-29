from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
from django.test import SimpleTestCase

from apps.exporter.services import ExportService


class ExportServiceTests(SimpleTestCase):

    def setUp(self):
        self.service = ExportService()

        self.dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

    def test_supported_formats(self):
        self.assertEqual(
            self.service.supported_formats(),
            [
                "csv",
                "pdf",
                "xlsm",
                "xlsx",
                "xltm",
                "xltx",
            ],
        )

    def test_rejects_non_string_format(self):
        with self.assertRaisesMessage(
            ValueError,
            "Export format must be a string.",
        ):
            self.service.export(
                self.dataframe,
                "output.csv",
                None,
            )

    def test_rejects_empty_format(self):
        with self.assertRaisesMessage(
            ValueError,
            "Export format cannot be empty.",
        ):
            self.service.export(
                self.dataframe,
                "output.csv",
                "   ",
            )

    def test_rejects_unsupported_format(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported export format 'json'.",
        ):
            self.service.export(
                self.dataframe,
                "output.json",
                "json",
            )

    def test_format_is_case_insensitive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"

            result = self.service.export(
                self.dataframe,
                path,
                "CSV",
            )

            self.assertEqual(
                result,
                path,
            )

            self.assertTrue(
                path.exists()
            )


class ExcelExportTests(SimpleTestCase):

    def setUp(self):
        self.service = ExportService()

        self.dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

    def test_exports_excel_file(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

        service = ExportService()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.xlsx"

            result = service.export(
                dataframe,
                path,
                "xlsx",
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

            loaded = pd.read_excel(
                path,
                engine="openpyxl",
            )

            pd.testing.assert_frame_equal(
                loaded,
                dataframe,
            )
    def test_exports_xlsm(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

        service = ExportService()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.xlsm"

            result = service.export(
                dataframe,
                path,
                "xlsm",
            )

            self.assertEqual(
                result,
                path,
            )

            self.assertTrue(
                path.exists()
            )

    def test_exports_xltx(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani"],
                "age": [20],
            }
        )

        service = ExportService()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.xltx"

            result = service.export(
                dataframe,
                path,
                "xltx",
            )

            self.assertEqual(
                result,
                path,
            )

            self.assertTrue(
                path.exists()
            )

    def test_exports_xltm(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani"],
                "age": [20],
            }
        )

        service = ExportService()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.xltm"

            result = service.export(
                dataframe,
                path,
                "xltm",
            )

            self.assertEqual(
                result,
                path,
            )

            self.assertTrue(
                path.exists()
            )


    def test_all_supported_formats_are_registered(self):
        supported = self.service.supported_formats()

        self.assertEqual(
            supported,
            [
                "csv",
                "pdf",
                "xlsm",
                "xlsx",
                "xltm",
                "xltx",
            ],
        )

    def test_export_format_is_normalized_before_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.xlsx"

            result = self.service.export(
                self.dataframe,
                path,
                "  XLSX  ",
            )

            self.assertEqual(
                result,
                path,
            )

            self.assertTrue(
                path.exists()
            )

    def test_excel_round_trip(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

        service = ExportService()

        with tempfile.TemporaryDirectory() as directory:
            path = (
                Path(directory)
                / "round_trip.xlsx"
            )

            service.export(
                dataframe,
                path,
                "xlsx",
            )

            loaded = pd.read_excel(
                path,
                engine="openpyxl",
            )

            pd.testing.assert_frame_equal(
                loaded,
                dataframe,
            )

    def test_service_uses_writer_registry(self):
        from apps.exporter.writers import WRITERS

        self.assertIs(
            self.service.writers,
            WRITERS,
        )

    def test_get_writer_returns_registered_writer(self):
        writer = self.service.get_writer("csv")

        self.assertIs(
            writer,
            self.service.writers["csv"],
        )

    def test_get_writer_normalizes_format(self):
        writer = self.service.get_writer("  CSV  ")

        self.assertIs(
            writer,
            self.service.writers["csv"],
        )

    def test_get_writer_rejects_unsupported_format(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported export format 'json'.",
        ):
            self.service.get_writer("json")