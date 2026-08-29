from __future__ import annotations

from django.test import SimpleTestCase

from apps.importer.excel_formats import (
    EXCEL_FORMATS,
    exportable_excel_extensions,
    get_excel_format,
    supported_excel_extensions,
)


class ExcelFormatTests(SimpleTestCase):

    def test_supported_extensions(self):
        self.assertEqual(
            set(supported_excel_extensions()),
            {
                ".xlsx",
                ".xlsm",
                ".xltx",
                ".xltm",
                ".xlsb",
                ".xlam",
            },
        )

    def test_exportable_extensions(self):
        self.assertEqual(
            set(exportable_excel_extensions()),
            {
                ".xlsx",
                ".xlsm",
                ".xltx",
                ".xltm",
            },
        )

    def test_xlsx_configuration(self):
        excel_format = get_excel_format(
            ".xlsx"
        )

        self.assertEqual(
            excel_format.reader_engine,
            "openpyxl",
        )

        self.assertEqual(
            excel_format.writer_engine,
            "openpyxl",
        )

        self.assertTrue(
            excel_format.exportable
        )

    def test_xlsm_configuration(self):
        excel_format = get_excel_format(
            ".xlsm"
        )

        self.assertEqual(
            excel_format.reader_engine,
            "openpyxl",
        )

        self.assertEqual(
            excel_format.writer_engine,
            "openpyxl",
        )

        self.assertTrue(
            excel_format.exportable
        )

        self.assertTrue(
            excel_format.macro_enabled
        )

    def test_xlsb_is_readable_but_not_exportable(self):
        excel_format = get_excel_format(
            ".xlsb"
        )

        self.assertEqual(
            excel_format.reader_engine,
            "pyxlsb",
        )

        self.assertIsNone(
            excel_format.writer_engine
        )

        self.assertFalse(
            excel_format.exportable
        )

    def test_xlam_is_not_imported_or_exported_as_dataset(self):
        excel_format = get_excel_format(
            ".xlam"
        )

        self.assertIsNone(
            excel_format.reader_engine
        )

        self.assertIsNone(
            excel_format.writer_engine
        )

        self.assertFalse(
            excel_format.exportable
        )

    def test_registry_contains_only_known_formats(self):
        self.assertEqual(
            set(EXCEL_FORMATS.keys()),
            {
                ".xlsx",
                ".xlsm",
                ".xltx",
                ".xltm",
                ".xlsb",
                ".xlam",
            },
        )

    def test_extension_lookup_is_case_insensitive(self):
        excel_format = get_excel_format(
            ".XLSX"
        )

        self.assertEqual(
            excel_format.extension,
            ".xlsx",
        )

    def test_format_types(self):
        expected = {
            ".xlsx": "excel_standard",
            ".xlsm": "excel_macro",
            ".xltx": "excel_template",
            ".xltm": "excel_template_macro",
            ".xlsb": "excel_binary",
            ".xlam": "excel_addin",
        }

        for extension, expected_type in expected.items():
            with self.subTest(extension=extension):
                excel_format = get_excel_format(
                    extension
                )

                self.assertEqual(
                    excel_format.format_type,
                    expected_type,
                )

    def test_template_metadata(self):
        self.assertFalse(
            get_excel_format(".xlsx").template
        )

        self.assertFalse(
            get_excel_format(".xlsm").template
        )

        self.assertTrue(
            get_excel_format(".xltx").template
        )

        self.assertTrue(
            get_excel_format(".xltm").template
        )

    def test_addin_metadata(self):
        excel_format = get_excel_format(
            ".xlam"
        )

        self.assertTrue(
            excel_format.addin
        )

        self.assertTrue(
            excel_format.macro_enabled
        )

    def test_macro_metadata(self):
        self.assertFalse(
            get_excel_format(".xlsx").macro_enabled
        )

        self.assertTrue(
            get_excel_format(".xlsm").macro_enabled
        )

        self.assertFalse(
            get_excel_format(".xltx").macro_enabled
        )

        self.assertTrue(
            get_excel_format(".xltm").macro_enabled
        )

        self.assertFalse(
            get_excel_format(".xlsb").macro_enabled
        )

    def test_rejects_unsupported_extension(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported Excel extension: .csv",
        ):
            get_excel_format(".csv")