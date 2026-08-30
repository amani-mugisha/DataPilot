from __future__ import annotations

import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Iterable

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .base_writer import BaseWriter


logger = logging.getLogger(__name__)


class PDFWriter(BaseWriter):
    """
    Generate professional DataPilot PDF cleaning reports.

    The PDF is intentionally a report rather than a raw spreadsheet
    export. It contains:

        - report title
        - source filename
        - generation timestamp
        - dataset dimensions
        - cleaned-data preview
        - footer

    The writer accepts the same interface used by ExportService.
    """

    format_name = "pdf"

    PAGE_SIZE = landscape(A4)

    MARGIN_LEFT = 10 * mm
    MARGIN_RIGHT = 10 * mm
    MARGIN_TOP = 12 * mm
    MARGIN_BOTTOM = 12 * mm

    TABLE_FONT_SIZE = 7
    TABLE_HEADER_FONT_SIZE = 7
    TABLE_CELL_PADDING = 4

    # Prevent enormous datasets from creating huge PDFs.
    MAX_PREVIEW_ROWS = 100

    # Prevent a single cell from making the PDF layout unusable.
    MAX_CELL_LENGTH = 120

    HEADER_BACKGROUND = colors.HexColor("#171A1F")
    HEADER_TEXT = colors.white
    GRID_COLOR = colors.HexColor("#DEE1E4")
    BODY_TEXT = colors.HexColor("#252A31")
    MUTED_TEXT = colors.HexColor("#5E6672")
    REPORT_BORDER = colors.HexColor("#D5D9DE")

    # Public API
    def write(
        self,
        dataframe: pd.DataFrame,
        output_path: str | Path,
        *,
        original_filename: str = "dataset.csv",
        statistics: dict | None = None,
        **kwargs,
    ) -> Path:
        """
        Generate a DataPilot PDF report.

        Args:
            dataframe:
                Cleaned DataFrame.

            output_path:
                Destination PDF path.

            original_filename:
                Name of the source dataset.

            statistics:
                Optional cleaning statistics.

            **kwargs:
                Reserved for future PDF options.

        Returns:
            Path to the generated PDF.
        """

        if dataframe is None:
            raise ValueError(
                "PDFWriter.write() requires a DataFrame."
            )

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(
                "PDFWriter.write() requires a pandas DataFrame."
            )

        path = Path(output_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        pdf_buffer = self._build_pdf(
            filename=original_filename,
            dataframe=dataframe,
            statistics=statistics,
        )

        path.write_bytes(
            pdf_buffer.getvalue()
        )

        self._validate_output(path)

        return path

    # PDF construction
    def _build_pdf(
        self,
        *,
        filename: str,
        dataframe: pd.DataFrame,
        statistics: dict | None = None,
    ) -> BytesIO:
        """
        Build the complete PDF document.

        Every element passed to ReportLab is explicitly flattened and
        validated as a Flowable. This prevents nested-list errors.
        """

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=self.PAGE_SIZE,
            leftMargin=self.MARGIN_LEFT,
            rightMargin=self.MARGIN_RIGHT,
            topMargin=self.MARGIN_TOP,
            bottomMargin=self.MARGIN_BOTTOM,
            title=f"DataPilot Cleaning Report — {filename}",
            author="DataPilot",
            subject="Cleaned dataset report",
        )

        elements = []

        # Header
        self._append_flowables(
            elements,
            self._build_header(
                filename=filename,
                dataframe=dataframe,
                statistics=statistics,
            ),
        )

        elements.append(
            Spacer(1, 10)
        )

        # Dataset preview section
        elements.append(
            self._section_title(
                "Cleaned Dataset Preview"
            )
        )

        elements.append(
            Spacer(1, 5)
        )

        elements.append(
            self._build_table(dataframe)
        )

        # Preview note
        if len(dataframe) > self.MAX_PREVIEW_ROWS:
            elements.append(
                Spacer(1, 6)
            )

            elements.append(
                Paragraph(
                    self._escape(
                        f"Showing the first "
                        f"{self.MAX_PREVIEW_ROWS:,} rows "
                        f"of {len(dataframe):,} cleaned rows."
                    ),
                    self._muted_style(),
                )
            )

        elements.append(
            Spacer(1, 12)
        )

        # Footer
        self._append_flowables(
            elements,
            self._build_footer(),
        )

        self._validate_flowables(
            elements
        )

        try:
            document.build(
                elements
            )

        except Exception:
            logger.exception(
                "Failed to build PDF report for '%s'",
                filename,
            )
            raise

        buffer.seek(0)

        return buffer

    # Header
    def _build_header(
        self,
        *,
        filename: str,
        dataframe: pd.DataFrame,
        statistics: dict | None,
    ) -> list:
        """
        Build report header flowables.
        """

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DataPilotReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=self.HEADER_BACKGROUND,
            spaceAfter=4,
        )

        meta_style = ParagraphStyle(
            "DataPilotReportMeta",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=self.MUTED_TEXT,
        )

        summary_style = ParagraphStyle(
            "DataPilotReportSummary",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=self.BODY_TEXT,
        )

        original_rows = (
            statistics.get(
                "original_rows"
            )
            if statistics
            else len(dataframe)
        )

        original_columns = (
            statistics.get(
                "original_columns"
            )
            if statistics
            else len(dataframe.columns)
        )

        final_rows = (
            statistics.get(
                "final_rows"
            )
            if statistics
            else len(dataframe)
        )

        final_columns = (
            statistics.get(
                "final_columns"
            )
            if statistics
            else len(dataframe.columns)
        )

        rows_removed = (
            statistics.get(
                "rows_removed",
                max(
                    original_rows - final_rows,
                    0,
                ),
            )
            if statistics
            else max(
                original_rows - final_rows,
                0,
            )
        )

        missing_values = (
            statistics.get(
                "missing_values",
                0,
            )
            if statistics
            else 0
        )

        duplicates_removed = (
            statistics.get(
                "duplicates_removed",
                0,
            )
            if statistics
            else 0
        )

        empty_rows_removed = (
            statistics.get(
                "empty_rows_removed",
                0,
            )
            if statistics
            else 0
        )

        generated_at = datetime.now().strftime(
            "%B %d, %Y at %H:%M"
        )

        elements = [
            Paragraph(
                "DataPilot — Cleaning Report",
                title_style,
            ),
            Paragraph(
                (
                    "<b>Source file:</b> "
                    f"{self._escape(filename)}"
                ),
                summary_style,
            ),
            Spacer(1, 3),
            Paragraph(
                (
                    "<b>Generated:</b> "
                    f"{self._escape(generated_at)}"
                ),
                meta_style,
            ),
            Spacer(1, 8),
        ]

        summary_data = [
            [
                self._summary_cell(
                    "Original Rows",
                    f"{original_rows:,}",
                ),
                self._summary_cell(
                    "Cleaned Rows",
                    f"{final_rows:,}",
                ),
                self._summary_cell(
                    "Rows Removed",
                    f"{rows_removed:,}",
                ),
                self._summary_cell(
                    "Columns",
                    f"{final_columns:,}",
                ),
            ],
            [
                self._summary_cell(
                    "Missing Values",
                    f"{missing_values:,}",
                ),
                self._summary_cell(
                    "Duplicates Removed",
                    f"{duplicates_removed:,}",
                ),
                self._summary_cell(
                    "Empty Rows Removed",
                    f"{empty_rows_removed:,}",
                ),
                self._summary_cell(
                    "Original Columns",
                    f"{original_columns:,}",
                ),
            ],
        ]

        summary_table = Table(
            summary_data,
            colWidths=[
                65 * mm,
                65 * mm,
                65 * mm,
                65 * mm,
            ],
            hAlign="LEFT",
        )

        summary_table.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        self.REPORT_BORDER,
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        self.REPORT_BORDER,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        elements.append(
            summary_table
        )

        return elements

    # Dataset table
    def _build_table(
        self,
        dataframe: pd.DataFrame,
    ) -> Table:
        """
        Build a paginated preview table.
        """

        if dataframe.empty:
            table = Table(
                [
                    [
                        Paragraph(
                            "No cleaned rows to display.",
                            self._table_body_style(),
                        )
                    ]
                ]
            )

            table.setStyle(
                self._table_style(
                    has_header=False
                )
            )

            return table

        preview = dataframe.head(
            self.MAX_PREVIEW_ROWS
        ).copy()

        display_df = (
            preview
            .fillna("")
            .astype(str)
        )

        headers = [
            self._truncate_text(
                column
            )
            for column in display_df.columns
        ]

        table_data = [
            [
                Paragraph(
                    self._escape(header),
                    self._table_header_style(),
                )
                for header in headers
            ]
        ]

        for row in display_df.itertuples(
            index=False,
            name=None,
        ):
            table_data.append(
                [
                    Paragraph(
                        self._escape(
                            self._truncate_text(value)
                        ),
                        self._table_body_style(),
                    )
                    for value in row
                ]
            )

        column_count = len(
            display_df.columns
        )

        table = Table(
            table_data,
            colWidths=self._column_widths(
                column_count
            ),
            repeatRows=1,
            hAlign="LEFT",
        )

        table.setStyle(
            self._table_style(
                has_header=True
            )
        )

        return table

    # Styles
    def _table_header_style(self) -> ParagraphStyle:
        return ParagraphStyle(
            "DataPilotTableHeader",
            fontName="Helvetica-Bold",
            fontSize=self.TABLE_HEADER_FONT_SIZE,
            leading=9,
            textColor=self.HEADER_TEXT,
            alignment=TA_LEFT,
        )

    def _table_body_style(self) -> ParagraphStyle:
        return ParagraphStyle(
            "DataPilotTableBody",
            fontName="Helvetica",
            fontSize=self.TABLE_FONT_SIZE,
            leading=9,
            textColor=self.BODY_TEXT,
            alignment=TA_LEFT,
        )

    def _muted_style(self) -> ParagraphStyle:
        return ParagraphStyle(
            "DataPilotMuted",
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=self.MUTED_TEXT,
        )

    def _section_title(
        self,
        text: str,
    ) -> Paragraph:
        style = ParagraphStyle(
            "DataPilotSectionTitle",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=self.HEADER_BACKGROUND,
            alignment=TA_LEFT,
        )

        return Paragraph(
            self._escape(text),
            style,
        )

    def _summary_cell(
        self,
        label: str,
        value: str,
    ) -> Paragraph:
        style = ParagraphStyle(
            "DataPilotSummaryCell",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=self.BODY_TEXT,
        )

        return Paragraph(
            (
                f"<b>{self._escape(label)}</b><br/>"
                f"{self._escape(value)}"
            ),
            style,
        )

    # Table formatting
    def _column_widths(
        self,
        column_count: int,
    ) -> list[float] | None:
        """
        Calculate equal-width columns that fit the page.
        """

        if column_count <= 0:
            return None

        usable_width = (
            self.PAGE_SIZE[0]
            - self.MARGIN_LEFT
            - self.MARGIN_RIGHT
        )

        width = usable_width / column_count

        return [
            width
            for _ in range(column_count)
        ]

    def _table_style(
        self,
        *,
        has_header: bool,
    ) -> TableStyle:
        commands = [
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                self.GRID_COLOR,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                self.TABLE_CELL_PADDING,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                self.TABLE_CELL_PADDING,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                self.TABLE_CELL_PADDING,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                self.TABLE_CELL_PADDING,
            ),
        ]

        if has_header:
            commands.extend(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        self.HEADER_BACKGROUND,
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        self.HEADER_TEXT,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, 0),
                        self.TABLE_HEADER_FONT_SIZE,
                    ),
                ]
            )

        return TableStyle(
            commands
        )

    # Footer
    def _build_footer(self) -> list:
        """
        Build footer flowables.

        This deliberately returns a flat list of Flowables.
        """

        style = ParagraphStyle(
            "DataPilotFooter",
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=self.MUTED_TEXT,
            alignment=TA_CENTER,
        )

        return [
            Paragraph(
                "Generated by DataPilot",
                style,
            )
        ]

    # Flowable safety
    @staticmethod
    def _append_flowables(
        target: list,
        flowables: Iterable,
    ) -> None:
        """
        Append Flowables to a document while flattening nested
        iterables defensively.

        ReportLab requires every item in the story to be a Flowable.
        """

        for item in flowables:
            if isinstance(item, (list, tuple)):
                PDFWriter._append_flowables(
                    target,
                    item,
                )
            else:
                target.append(item)

    @staticmethod
    def _validate_flowables(
        flowables: list,
    ) -> None:
        """
        Fail early if a non-Flowable accidentally reaches ReportLab.
        """

        for index, flowable in enumerate(
            flowables
        ):
            if isinstance(
                flowable,
                (list, tuple),
            ):
                raise TypeError(
                    "PDF document contains a nested list "
                    f"at story index {index}."
                )

            if not hasattr(
                flowable,
                "getKeepWithNext",
            ):
                raise TypeError(
                    "PDF document contains an invalid "
                    f"Flowable at story index {index}: "
                    f"{type(flowable).__name__}."
                )

    # Text safety
    @classmethod
    def _truncate_text(
        cls,
        value,
    ) -> str:
        text = str(value)

        if len(text) <= cls.MAX_CELL_LENGTH:
            return text

        return (
            text[: cls.MAX_CELL_LENGTH - 1]
            + "…"
        )

    @staticmethod
    def _escape(
        text: str,
    ) -> str:
        """
        Escape text before placing it inside ReportLab Paragraphs.
        """

        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    # Output validation
    @staticmethod
    def _validate_output(
        path: Path,
    ) -> None:
        """
        Validate that a PDF was actually generated.
        """

        if not path.exists():
            raise RuntimeError(
                f"PDF export did not create output file: {path}"
            )

        if path.stat().st_size == 0:
            raise RuntimeError(
                f"PDF export created an empty file: {path}"
            )

        # PDF files begin with the %PDF signature.
        with path.open(
            "rb"
        ) as file:
            signature = file.read(5)

        if signature != b"%PDF-":
            raise RuntimeError(
                f"Generated file is not a valid PDF: {path}"
            )