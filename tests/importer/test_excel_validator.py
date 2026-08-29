from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from openpyxl import Workbook

from apps.importer.validators import BaseValidator, ExcelValidator


class ExcelValidatorTests(SimpleTestCase):

    def _create_xlsx(self) -> BytesIO:
        workbook = Workbook()

        worksheet = workbook.active
        worksheet.append(["name", "age"])
        worksheet.append(["Amani", 20])

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        return buffer

    def test_implements_base_validator(self):
        validator = ExcelValidator()

        self.assertIsInstance(
            validator,
            BaseValidator,
        )

    def test_accepts_valid_xlsx(self):
        validator = ExcelValidator()
        workbook = self._create_xlsx()

        validator.validate(
            workbook,
            filename="customers.xlsx",
        )

    def test_accepts_supported_excel_extensions(self):
        validator = ExcelValidator()

        for filename in (
            "customers.xlsx",
            "customers.xlsm",
            "template.xltx",
            "template.xltm",
            "data.xlsb",
            "addin.xlam",
        ):
            with self.subTest(filename=filename):
                validator.validate_filename(filename)

    def test_accepts_uppercase_extension(self):
        validator = ExcelValidator()

        validator.validate_filename(
            "CUSTOMERS.XLSX"
        )

    def test_rejects_empty_filename(self):
        validator = ExcelValidator()

        with self.assertRaisesMessage(
            ValueError,
            "Excel filename cannot be empty.",
        ):
            validator.validate_filename("")

    def test_rejects_unsupported_extension(self):
        validator = ExcelValidator()

        with self.assertRaisesMessage(
            ValueError,
            "Only Excel files are supported.",
        ):
            validator.validate_filename(
                "customers.csv"
            )

    def test_rejects_filename_without_extension(self):
        validator = ExcelValidator()

        with self.assertRaisesMessage(
            ValueError,
            "Unsupported file format: unknown",
        ):
            validator.validate_filename(
                "customers"
            )

    def test_rejects_negative_size(self):
        validator = ExcelValidator()

        with self.assertRaisesMessage(
            ValueError,
            "Excel file size cannot be negative.",
        ):
            validator.validate_size(-1)

    def test_accepts_maximum_size(self):
        validator = ExcelValidator()

        validator.validate_size(
            validator.MAX_FILE_SIZE
        )

    def test_rejects_file_over_50mb(self):
        validator = ExcelValidator()

        with self.assertRaisesMessage(
            ValueError,
            "The maximum Excel file size is 50MB.",
        ):
            validator.validate_size(
                validator.MAX_FILE_SIZE + 1
            )

    def test_rejects_none(self):
        validator = ExcelValidator()

        with self.assertRaisesMessage(
            ValueError,
            "ExcelValidator.validate() requires a file.",
        ):
            validator.validate(
                None,
                filename="customers.xlsx",
            )

    def test_rejects_missing_file(self):
        validator = ExcelValidator()

        with TemporaryDirectory() as directory:
            path = Path(directory) / "missing.xlsx"

            with self.assertRaisesMessage(
                ValueError,
                "The Excel file does not exist.",
            ):
                validator.validate(
                    path,
                    filename="missing.xlsx",
                )

    def test_rejects_invalid_ooxml_package(self):
        validator = ExcelValidator()

        invalid_file = BytesIO(
            b"this is not an excel workbook"
        )

        with self.assertRaisesMessage(
            ValueError,
            "File is not a valid Excel OOXML package.",
        ):
            validator.validate(
                invalid_file,
                filename="customers.xlsx",
            )

    def test_rejects_none_file(self):
        validator = ExcelValidator()

        with self.assertRaisesMessage(
            ValueError,
            "ExcelValidator.validate() requires a file.",
        ):
            validator.validate(
                None,
                filename="customers.xlsx",
            )

    def test_rejects_ooxml_package_without_workbook(self):
        from zipfile import ZipFile

        buffer = BytesIO()

        with ZipFile(
            buffer,
            "w",
        ) as archive:
            archive.writestr(
                "[Content_Types].xml",
                "<Types/>",
            )
            archive.writestr(
                "_rels/.rels",
                "<Relationships/>",
            )

        buffer.seek(0)

        validator = ExcelValidator()

        with self.assertRaisesMessage(
            ValueError,
            "The Excel workbook structure is invalid.",
        ):
            validator.validate(
                buffer,
                filename="customers.xlsx",
            )
