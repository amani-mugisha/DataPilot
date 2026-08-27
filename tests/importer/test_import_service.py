from __future__ import annotations

from io import StringIO

import pandas as pd
from django.test import SimpleTestCase

from apps.importer.services import ImportService


class ImportServiceTests(SimpleTestCase):

    def setUp(self):
        self.service = ImportService()

    def test_supported_formats(self):
        self.assertEqual(
            self.service.supported_formats(),
            ["csv"],
        )

    def test_detect_csv(self):
        detected = self.service.detect(
            "customers.csv"
        )

        self.assertEqual(
            detected.format,
            "csv",
        )

        self.assertEqual(
            detected.extension,
            ".csv",
        )

    def test_validate_csv(self):
        csv_data = StringIO(
            "name,age\n"
            "Amani,20\n"
            "John,25\n"
        )

        detected = self.service.validate(
            file_path=csv_data,
            filename="customers.csv",
        )

        self.assertEqual(
            detected.format,
            "csv",
        )

    def test_read_csv(self):
        csv_data = StringIO(
            "name,age\n"
            "Amani,20\n"
            "John,25\n"
        )

        dataframe, detected = self.service.read(
            file_path=csv_data,
            filename="customers.csv",
        )

        self.assertIsInstance(
            dataframe,
            pd.DataFrame,
        )

        self.assertEqual(
            detected.format,
            "csv",
        )

        self.assertEqual(
            list(dataframe.columns),
            ["name", "age"],
        )

        self.assertEqual(
            len(dataframe),
            2,
        )

    def test_read_preserves_missing_values(self):
        csv_data = StringIO(
            "name,age\n"
            "Amani,20\n"
            "John,\n"
        )

        dataframe, _ = self.service.read(
            file_path=csv_data,
            filename="customers.csv",
        )

        self.assertTrue(
            pd.isna(
                dataframe.loc[1, "age"]
            )
        )

    def test_rejects_non_csv(self):
        csv_data = StringIO(
            "name,age\n"
            "Amani,20\n"
        )

        with self.assertRaisesMessage(
            ValueError,
            "Unsupported file format: .xlsx",
        ):
            self.service.read(
                file_path=csv_data,
                filename="customers.xlsx",
            )

    def test_rejects_empty_csv(self):
        csv_data = StringIO("")

        with self.assertRaisesMessage(
            ValueError,
            "The CSV file is empty.",
        ):
            self.service.read(
                file_path=csv_data,
                filename="customers.csv",
            )

    def test_reader_registry_matches_validator_registry(self):
        self.assertEqual(
            set(self.service.readers),
            set(self.service.validators),
        )

    def test_registered_csv_reader(self):
        self.assertIn(
            "csv",
            self.service.readers,
        )

        self.assertEqual(
            self.service.readers["csv"].format_name,
            "csv",
        )

    def test_registered_csv_validator(self):
        self.assertIn(
            "csv",
            self.service.validators,
        )

        self.assertEqual(
            self.service.validators["csv"].format_name,
            "csv",
        )