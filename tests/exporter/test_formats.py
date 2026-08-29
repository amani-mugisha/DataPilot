from django.test import SimpleTestCase

from apps.exporter.formats import (
    EXCEL_EXPORT_FORMATS,
    SUPPORTED_EXPORT_FORMATS,
    is_excel_export_format,
    normalize_export_format,
)


class ExportFormatTests(SimpleTestCase):

    def test_supported_export_formats(self):
        self.assertEqual(
            SUPPORTED_EXPORT_FORMATS,
            {
                "csv",
                "pdf",
                "xlsx",
                "xlsm",
                "xltx",
                "xltm",
            },
        )

    def test_excel_export_formats(self):
        self.assertEqual(
            EXCEL_EXPORT_FORMATS,
            {
                "xlsx",
                "xlsm",
                "xltx",
                "xltm",
            },
        )

    def test_normalizes_format(self):
        self.assertEqual(
            normalize_export_format(" XLSX "),
            "xlsx",
        )

    def test_rejects_non_string(self):
        with self.assertRaisesMessage(
            ValueError,
            "Export format must be a string.",
        ):
            normalize_export_format(None)

    def test_rejects_empty_format(self):
        with self.assertRaisesMessage(
            ValueError,
            "Export format cannot be empty.",
        ):
            normalize_export_format("   ")

    def test_rejects_unsupported_format(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported export format 'json'.",
        ):
            normalize_export_format("json")

    def test_detects_excel_format(self):
        self.assertTrue(
            is_excel_export_format("xlsx")
        )

    def test_detects_non_excel_format(self):
        self.assertFalse(
            is_excel_export_format("csv")
        )