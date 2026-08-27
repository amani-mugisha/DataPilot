from __future__ import annotations

import pandas as pd
from django.test import SimpleTestCase

from apps.cleaner.services.cleaner import clean_dataframe


class CleanerTests(SimpleTestCase):

    def test_returns_dataframe_and_statistics(self):
        dataframe = pd.DataFrame(
            {
                "Name": ["Amani", "John"],
                "Age": [20, 25],
            }
        )

        cleaned, statistics = clean_dataframe(dataframe)

        self.assertIsInstance(
            cleaned,
            pd.DataFrame,
        )

        self.assertIsInstance(
            statistics,
            dict,
        )

    def test_standardizes_column_names(self):
        dataframe = pd.DataFrame(
            {
                " First Name ": ["Amani"],
                "AGE": [20],
                "Email Address": ["amani@example.com"],
            }
        )

        cleaned, _ = clean_dataframe(dataframe)

        self.assertEqual(
            list(cleaned.columns),
            [
                "first_name",
                "age",
                "email_address",
            ],
        )

    def test_removes_completely_empty_rows(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani", None, "John"],
                "age": [20, None, 25],
            }
        )

        cleaned, statistics = clean_dataframe(dataframe)

        self.assertEqual(
            len(cleaned),
            2,
        )

        self.assertEqual(
            statistics["empty_rows_removed"],
            1,
        )

    def test_removes_completely_empty_rows(self):
        dataframe = pd.DataFrame(
            {
                "name": ["Amani", None, "John"],
                "age": [20, None, 25],
            }
        )

        cleaned, statistics = clean_dataframe(dataframe)

        self.assertEqual(
            len(cleaned),
            2,
        )

        self.assertEqual(
            statistics["empty_rows_removed"],
            1,
        )

    def test_normalizes_missing_markers(self):
        dataframe = pd.DataFrame(
            {
                "name": [
                    "Amani",
                    "N/A",
                    "null",
                    "-",
                ],
            }
        )

        cleaned, _ = clean_dataframe(dataframe)

        self.assertFalse(
            cleaned["name"].isna().any()
        )

    def test_strips_text_whitespace(self):
        dataframe = pd.DataFrame(
            {
                "name": [
                    "  Amani  ",
                    " John",
                    "Mary ",
                ],
            }
        )

        cleaned, _ = clean_dataframe(dataframe)

        self.assertEqual(
            list(cleaned["name"]),
            [
                "Amani",
                "John",
                "Mary",
            ],
        )

    def test_fills_missing_numeric_values_with_median(self):
        dataframe = pd.DataFrame(
            {
                "age": [
                    20,
                    None,
                    30,
                ],
                "name": [
                    "Amani",
                    "John",
                    "Mary",
                ],
            }
        )

        cleaned, _ = clean_dataframe(dataframe)

        self.assertEqual(
            cleaned["age"].tolist(),
            [20, 25, 30],
        )

    def test_fills_missing_text_values(self):
        dataframe = pd.DataFrame(
            {
                "name": [
                    "Amani",
                    None,
                    "John",
                ],
                "age": [
                    20,
                    25,
                    30,
                ],
            }
        )

        cleaned, _ = clean_dataframe(dataframe)

        self.assertEqual(
            cleaned["name"].tolist(),
            [
                "Amani",
                "Unknown",
                "John",
            ],
        )

    def test_reports_missing_values(self):
        dataframe = pd.DataFrame(
            {
                "name": [
                    "Amani",
                    None,
                ],
            }
        )

        _, statistics = clean_dataframe(dataframe)

        self.assertGreaterEqual(
            statistics["missing_values"],
            1,
        )

        self.assertTrue(
            any(
                finding["finding_type"] == "missing"
                for finding in statistics["findings"]
            )
        )

    def test_reports_duplicates(self):
        dataframe = pd.DataFrame(
            {
                "name": [
                    "Amani",
                    "Amani",
                ],
            }
        )

        _, statistics = clean_dataframe(dataframe)

        self.assertEqual(
            statistics["duplicates_removed"],
            1,
        )

        self.assertTrue(
            any(
                finding["finding_type"] == "duplicate"
                for finding in statistics["findings"]
            )
        )

    def test_reports_empty_rows(self):
        dataframe = pd.DataFrame(
            {
                "name": [
                    "Amani",
                    None,
                ],
                "age": [
                    20,
                    None,
                ],
            }
        )

        _, statistics = clean_dataframe(dataframe)

        self.assertEqual(
            statistics["empty_rows_removed"],
            1,
        )

        self.assertTrue(
            any(
                finding["finding_type"] == "invalid"
                for finding in statistics["findings"]
            )
        )

    def test_does_not_modify_original_dataframe(self):
        dataframe = pd.DataFrame(
            {
                "Name": ["  Amani  "],
                "Age": [20],
            }
        )

        original = dataframe.copy(deep=True)

        clean_dataframe(dataframe)

        pd.testing.assert_frame_equal(
            dataframe,
            original,
        )

    def test_statistics_track_rows(self):
        dataframe = pd.DataFrame(
            {
                "name": [
                    "Amani",
                    "Amani",
                    None,
                ],
            }
        )

        _, statistics = clean_dataframe(dataframe)

        self.assertEqual(
            statistics["original_rows"],
            3,
        )

        self.assertEqual(
            statistics["final_rows"],
            1,
        )

        self.assertEqual(
            statistics["rows_removed"],
            2,
        )