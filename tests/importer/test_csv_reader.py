from __future__ import annotations

from io import StringIO

import pandas as pd
from django.test import SimpleTestCase

from apps.importer.readers import CSVReader


class CSVReaderTests(SimpleTestCase):

    def setUp(self):
        self.reader = CSVReader()

    def test_reads_csv(self):
        csv_data = StringIO(
            "name,age\n"
            "Amani,20\n"
            "John,25\n"
        )

        dataframe = self.reader.read(csv_data)

        self.assertIsInstance(
            dataframe,
            pd.DataFrame,
        )

        self.assertEqual(
            list(dataframe.columns),
            ["name", "age"],
        )

        self.assertEqual(
            len(dataframe),
            2,
        )

    def test_preserves_missing_values(self):
        csv_data = StringIO(
            "name,age\n"
            "Amani,20\n"
            "John,\n"
        )

        dataframe = self.reader.read(csv_data)

        self.assertTrue(
            pd.isna(dataframe.loc[1, "age"])
        )

    def test_reads_utf8_text(self):
        csv_data = StringIO(
            "name,city\n"
            "Amani,Kigali\n"
            "Jean,Butare\n"
        )

        dataframe = self.reader.read(csv_data)

        self.assertEqual(
            dataframe.loc[0, "city"],
            "Kigali",
        )

    def test_rejects_empty_csv(self):
        csv_data = StringIO("")

        with self.assertRaisesMessage(
            ValueError,
            "The CSV file is empty.",
        ):
            self.reader.read(csv_data)

    def test_rejects_none(self):
        with self.assertRaisesMessage(
            ValueError,
            "CSVReader.read() requires a file.",
        ):
            self.reader.read(None)
