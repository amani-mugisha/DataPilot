from __future__ import annotations

import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd

from .base_writer import BaseWriter

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


PAGE_SIZE = landscape(A4)

MARGIN_LEFT = 10 * mm
MARGIN_RIGHT = 10 * mm
MARGIN_TOP = 12 * mm
MARGIN_BOTTOM = 12 * mm

TABLE_FONT_SIZE = 7
TABLE_CELL_PADDING = 4

COLOR_HEADER_BG = colors.HexColor("#171A1F")
COLOR_HEADER_TEXT = colors.white
COLOR_GRID = colors.HexColor("#DEE1E4")


class PDFWriter(BaseWriter):
    """Write a pandas DataFrame as a DataPilot PDF report."""

    format_name = "pdf"

    def write(
        self,
        dataframe: pd.DataFrame,
        output_path: str | Path,
        *,
        original_filename: str = "dataset.csv",
    ) -> Path:
        """Generate and save a PDF report."""

        if dataframe is None:
            raise ValueError(
                "PDFWriter.write() requires a DataFrame."
            )

        path = Path(output_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        pdf_buffer = self._build_pdf(
            original_filename,
            dataframe,
        )

        path.write_bytes(
            pdf_buffer.getvalue()
        )

        return path

    def _build_pdf(
        self,
        filename: str,
        dataframe: pd.DataFrame,
    ) -> BytesIO:

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=PAGE_SIZE,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=MARGIN_TOP,
            bottomMargin=MARGIN_BOTTOM,
            title=f"DataPilot Report — {filename}",
        )

        elements = [
            *self._build_header(
                filename,
                dataframe,
            ),
            Spacer(1, 12),
            self._build_table(dataframe),
            Spacer(1, 12),
            *self._build_footer(),
        ]

        try:
            document.build(elements)

        except Exception:
            logger.exception(
                "Failed to build PDF report for '%s'",
                filename,
            )
            raise

        buffer.seek(0)

        return buffer

    def _build_header(
        self,
        filename: str,
        dataframe: pd.DataFrame,
    ) -> list:

        styles = getSampleStyleSheet()

        meta_style = ParagraphStyle(
            "Meta",
            parent=styles["BodyText"],
            textColor=colors.HexColor("#4B515C"),
        )

        return [
            Paragraph(
                "DataPilot — Cleaned Dataset Report",
                styles["Title"],
            ),
            Spacer(1, 4),
            Paragraph(
                f"<b>Source file:</b> "
                f"{self._escape(filename)}",
                styles["BodyText"],
            ),
            Paragraph(
                f"<b>Rows:</b> {len(dataframe):,} "
                f"&nbsp;&nbsp;&nbsp; "
                f"<b>Columns:</b> "
                f"{len(dataframe.columns):,}",
                styles["BodyText"],
            ),
            Paragraph(
                f"Generated "
                f"{datetime.now():%B %d, %Y at %H:%M}",
                meta_style,
            ),
        ]

    def _build_table(
        self,
        dataframe: pd.DataFrame,
    ) -> Table:

        if dataframe.empty:
            return Table(
                [["No rows to display."]],
                style=self._table_style(),
            )

        display_df = (
            dataframe
            .fillna("")
            .astype(str)
        )

        table_data = [
            list(display_df.columns)
        ] + display_df.values.tolist()

        column_count = len(
            display_df.columns
        )

        table = Table(
            table_data,
            colWidths=self._column_widths(
                column_count
            ),
            repeatRows=1,
        )

        table.setStyle(
            self._table_style()
        )

        return table

    def _column_widths(
        self,
        column_count: int,
    ) -> list[float] | None:

        if column_count <= 0:
            return None

        usable_width = (
            PAGE_SIZE[0]
            - MARGIN_LEFT
            - MARGIN_RIGHT
        )

        return [
            usable_width / column_count
        ] * column_count

    def _table_style(self) -> TableStyle:

        return TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    COLOR_HEADER_BG,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    COLOR_HEADER_TEXT,
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
                    (-1, -1),
                    TABLE_FONT_SIZE,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    COLOR_GRID,
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
                    TABLE_CELL_PADDING,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    TABLE_CELL_PADDING,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    TABLE_CELL_PADDING,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    TABLE_CELL_PADDING,
                ),
            ]
        )

    def _build_footer(self) -> list:

        styles = getSampleStyleSheet()

        return [
            Paragraph(
                "Generated by DataPilot",
                styles["BodyText"],
            )
        ]

    @staticmethod
    def _escape(text: str) -> str:

        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
