from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
from django.test import SimpleTestCase

from apps.exporter.writers import BaseWriter, CSVWriter


class CSVWriterTests(SimpleTestCase):

    def setUp(self):
        self.writer = CSVWriter()

    def test_implements_base_writer(self):
        self.assertIsInstance(
            self.writer,
            BaseWriter,
        )

        self.assertEqual(
            self.writer.format_name,
            "csv",
        )

    def test_writes_csv(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

        with TemporaryDirectory() as temp_dir:
            output_path = (
                Path(temp_dir) / "customers.csv"
            )

            result = self.writer.write(
                dataframe,
                output_path,
            )

            self.assertEqual(
                result,
                output_path,
            )

            self.assertTrue(
                output_path.exists()
            )

            loaded = pd.read_csv(
                output_path
            )

            pd.testing.assert_frame_equal(
                loaded,
                dataframe,
            )

    def test_creates_parent_directories(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani"],
            }
        )

        with TemporaryDirectory() as temp_dir:
            output_path = (
                Path(temp_dir)
                / "nested"
                / "deep"
                / "customers.csv"
            )

            self.writer.write(
                dataframe,
                output_path,
            )

            self.assertTrue(
                output_path.exists()
            )

    def test_does_not_write_dataframe_index(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani"],
            },
            index=[42],
        )

        with TemporaryDirectory() as temp_dir:
            output_path = (
                Path(temp_dir) / "customers.csv"
            )

            self.writer.write(
                dataframe,
                output_path,
            )

            loaded = pd.read_csv(
                output_path
            )

            self.assertEqual(
                list(loaded.columns),
                ["name"],
            )

            self.assertEqual(
                loaded.iloc[0]["name"],
                "Amani",
            )

    def test_supports_custom_separator(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani", "John"],
                "age": [20, 25],
            }
        )

        with TemporaryDirectory() as temp_dir:
            output_path = (
                Path(temp_dir) / "customers.csv"
            )

            self.writer.write(
                dataframe,
                output_path,
                sep=";",
            )

            loaded = pd.read_csv(
                output_path,
                sep=";",
            )

            pd.testing.assert_frame_equal(
                loaded,
                dataframe,
            )

    def test_supports_encoding(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani", "Jean"],
                "city": ["Kigali", "Butaré"],
            }
        )

        with TemporaryDirectory() as temp_dir:
            output_path = (
                Path(temp_dir) / "customers.csv"
            )

            self.writer.write(
                dataframe,
                output_path,
                encoding="utf-8",
            )

            loaded = pd.read_csv(
                output_path,
                encoding="utf-8",
            )

            pd.testing.assert_frame_equal(
                loaded,
                dataframe,
            )

    def test_rejects_none_dataframe(self):
        with self.assertRaisesMessage(
            ValueError,
            "CSVWriter.write() requires a DataFrame.",
        ):
            self.writer.write(
                None,
                "/tmp/output.csv",
            )

    def test_accepts_string_output_path(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani"],
            }
        )

        with TemporaryDirectory() as temp_dir:
            output_path = (
                Path(temp_dir) / "customers.csv"
            )

            result = self.writer.write(
                dataframe,
                str(output_path),
            )

            self.assertEqual(
                result,
                output_path
            )
