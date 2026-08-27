from __future__ import annotations

from django.test import SimpleTestCase

from apps.importer.readers import BaseReader, CSVReader
from apps.importer.validators import BaseValidator, CSVValidator


class ImporterContractTests(SimpleTestCase):

    def test_csv_reader_implements_base_reader(self):
        reader = CSVReader()

        self.assertIsInstance(
            reader,
            BaseReader,
        )

        self.assertEqual(
            reader.format_name,
            "csv",
        )

    def test_csv_validator_implements_base_validator(self):
        validator = CSVValidator()

        self.assertIsInstance(
            validator,
            BaseValidator,
        )

        self.assertEqual(
            validator.format_name,
            "csv",
        )
