from __future__ import annotations

from io import BytesIO

import pandas as pd
from django.test import SimpleTestCase
from openpyxl import Workbook

from apps.importer.readers import (
    BaseReader,
    ExcelReader,
)
from apps.importer.excel_formats import (
    get_excel_format,
)
from apps.importer.formats import (
    SUPPORTED_FORMATS,
)


class ExcelReaderTests(SimpleTestCase):

    def _create_workbook(self) -> BytesIO:
        workbook = Workbook()

        first = workbook.active
        first.title = "Customers"
        first.append(["name", "age"])
        first.append(["Amani", 20])
        first.append(["John", 25])

        second = workbook.create_sheet("Orders")
        second.append(["product", "price"])
        second.append(["Laptop", 1000])
        second.append(["Phone", 500])

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        return buffer

    def test_implements_base_reader(self):
        reader = ExcelReader()

        self.assertIsInstance(
            reader,
            BaseReader,
        )

        self.assertEqual(
            reader.format_name,
            "excel",
        )

    def test_reads_first_sheet_by_default(self):
        reader = ExcelReader()
        workbook = self._create_workbook()

        dataframe = reader.read(
            workbook,
            filename="customers.xlsx",
        )

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

    def test_reads_sheet_by_name(self):
        reader = ExcelReader()
        workbook = self._create_workbook()

        dataframe = reader.read(
            workbook,
            filename="customers.xlsx",
            sheet_name="Orders",
        )

        self.assertEqual(
            list(dataframe.columns),
            ["product", "price"],
        )

        self.assertEqual(
            len(dataframe),
            2,
        )

    def test_reads_sheet_by_index(self):
        reader = ExcelReader()
        workbook = self._create_workbook()

        dataframe = reader.read(
            workbook,
            filename="customers.xlsx",
            sheet_name=1,
        )

        self.assertEqual(
            list(dataframe.columns),
            ["product", "price"],
        )

    def test_lists_sheets(self):
        reader = ExcelReader()
        workbook = self._create_workbook()

        sheets = reader.list_sheets(
            workbook,
            filename="customers.xlsx",
        )

        self.assertEqual(
            sheets,
            ["Customers", "Orders"],
        )

    def test_rejects_unsupported_extension(self):
        reader = ExcelReader()
        workbook = self._create_workbook()

        with self.assertRaisesMessage(
            ValueError,
            "Unsupported Excel extension: .csv",
        ):
            reader.read(
                workbook,
                filename="customers.csv",
            )

    def test_requires_filename_for_file_like_object(self):
        reader = ExcelReader()
        workbook = self._create_workbook()

        with self.assertRaisesMessage(
            ValueError,
            "filename is required for Excel file-like objects.",
        ):
            reader.read(workbook)

    def test_rejects_invalid_sheet(self):
        reader = ExcelReader()
        workbook = self._create_workbook()

        with self.assertRaisesMessage(
            ValueError,
            "Could not read Excel file:",
        ):
            reader.read(
                workbook,
                filename="customers.xlsx",
                sheet_name="MissingSheet",
            )

    def test_supports_all_readable_excel_extensions(self):
        reader = ExcelReader()

        supported_extensions = {
            ".xlsx",
            ".xlsm",
            ".xltx",
            ".xltm",
            ".xlsb",
        }

        for extension in supported_extensions:
            with self.subTest(extension=extension):
                excel_format = get_excel_format(extension)

                self.assertIsNotNone(
                    excel_format.reader_engine
                )

                self.assertIn(
                    extension,
                    SUPPORTED_FORMATS,
                )