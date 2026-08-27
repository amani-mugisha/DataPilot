from __future__ import annotations

from tempfile import TemporaryDirectory
from pathlib import Path

from django.test import SimpleTestCase

from apps.importer.validators import CSVValidator


class CSVValidatorTests(SimpleTestCase):

    def setUp(self):
        self.validator = CSVValidator()

    def test_accepts_csv_filename(self):
        self.validator.validate_filename(
            "customers.csv"
        )

    def test_accepts_uppercase_csv_extension(self):
        self.validator.validate_filename(
            "customers.CSV"
        )

    def test_rejects_non_csv_filename(self):
        with self.assertRaisesMessage(
            ValueError,
            "Only CSV files are supported.",
        ):
            self.validator.validate_filename(
                "customers.xlsx"
            )

    def test_rejects_empty_filename(self):
        with self.assertRaisesMessage(
            ValueError,
            "CSV filename cannot be empty.",
        ):
            self.validator.validate_filename("")

    def test_accepts_valid_size(self):
        self.validator.validate_size(
            1024
        )

    def test_rejects_negative_size(self):
        with self.assertRaisesMessage(
            ValueError,
            "CSV file size cannot be negative.",
        ):
            self.validator.validate_size(-1)

    def test_rejects_file_over_50mb(self):
        with self.assertRaisesMessage(
            ValueError,
            "The maximum CSV file size is 50MB.",
        ):
            self.validator.validate_size(
                CSVValidator.MAX_FILE_SIZE + 1
            )

    def test_rejects_missing_file(self):
        with self.assertRaisesMessage(
            ValueError,
            "The CSV file does not exist.",
        ):
            self.validator.validate(
                "/tmp/does-not-exist-datapilot.csv"
            )

    def test_rejects_empty_file(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "empty.csv"
            path.touch()

            with self.assertRaisesMessage(
                ValueError,
                "The CSV file is empty.",
            ):
                self.validator.validate(path)

    def test_rejects_none(self):
        with self.assertRaisesMessage(
            ValueError,
            "CSVValidator.validate() requires a file.",
        ):
            self.validator.validate(None)
