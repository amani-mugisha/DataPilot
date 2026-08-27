from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.utils import timezone

from apps.cleaner.models import CleaningJob
from apps.cleaner.services.cleaner import clean_dataframe
from apps.datasets.models import Dataset
from apps.exporter.services import ExportService
from apps.cleaner.models import CleaningFinding
from apps.importer.services import ImportService

class CleaningPipeline:
    """
    Orchestrates the complete DataPilot cleaning workflow.

    Responsibilities:
        1. Load the imported dataset.
        2. Run the cleaning engine.
        3. Export the cleaned dataset.
        4. Generate the PDF report.
        5. Update the CleaningJob and Dataset records.

    The HTTP view should not need to know how these operations work.
    """

    def __init__(self, job: CleaningJob) -> None:
        self.job = job
        self.importer = ImportService()
        self.exporter = ExportService()

    def run(self) -> dict:
        """
        Execute the complete cleaning pipeline.

        Returns:
            Dictionary containing:
                - cleaned DataFrame
                - cleaning statistics
                - CSV filename
                - PDF filename
                - CSV path
                - PDF path
        """

        self._mark_processing()

        try:
            dataframe = self._load_dataframe()

            cleaned_dataframe, statistics = clean_dataframe(
                dataframe
            )

            output_paths = self._export_results(
                cleaned_dataframe
            )

            self._mark_complete(
                statistics=statistics,
                csv_filename=output_paths["csv_filename"],
            )

            return {
                "cleaned_dataframe": cleaned_dataframe,
                "statistics": statistics,
                **output_paths,
            }

        except Exception as exc:
            self._mark_failed(str(exc))
            raise

    # ------------------------------------------------------------------
    # Pipeline stages
    # ------------------------------------------------------------------

    def _load_dataframe(self) -> pd.DataFrame:
        """Load the original dataset through the importer."""

        if not self.job.original_file:
            raise ValueError(
                "Cleaning job does not have an original file."
            )

        dataframe, _detected = self.importer.read(
            file_path=self.job.original_file.path,
            filename=self.job.original_file.name,
        )

        return dataframe

    def _export_results(
        self,
        dataframe: pd.DataFrame,
    ) -> dict:
        """Export cleaned CSV and PDF report."""

        cleaned_dir = (
            Path(settings.MEDIA_ROOT) / "cleaned"
        )

        cleaned_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        original_filename = os.path.basename(
            self.job.original_file.name
        )

        base_name = os.path.splitext(
            original_filename
        )[0]

        csv_filename = (
            f"{base_name}_cleaned.csv"
        )

        pdf_filename = (
            f"{base_name}_cleaning_report.pdf"
        )

        csv_path = cleaned_dir / csv_filename
        pdf_path = cleaned_dir / pdf_filename

        self.exporter.export(
            dataframe,
            csv_path,
            "csv",
        )

        self.exporter.export(
            dataframe,
            pdf_path,
            "pdf",
            original_filename=original_filename,
        )

        return {
            "csv_filename": csv_filename,
            "pdf_filename": pdf_filename,
            "csv_path": str(csv_path),
            "pdf_path": str(pdf_path),
        }

    # ------------------------------------------------------------------
    # Database state
    # ------------------------------------------------------------------

    def _mark_processing(self) -> None:
        """Mark the job and dataset as processing."""

        self.job.status = CleaningJob.Status.PROCESSING

        self.job.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        if self.job.dataset:
            self.job.dataset.status = (
                Dataset.Status.PROCESSING
            )

            self.job.dataset.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

    def _mark_complete(
        self,
        statistics: dict,
        csv_filename: str,
    ) -> None:
        """Persist successful pipeline results."""

        fixed_issue_count = (
            statistics["missing_values"]
            + statistics["duplicates_removed"]
        )

        self.job.row_count = (
            statistics["original_rows"]
        )

        self.job.issues_found = (
            fixed_issue_count
        )

        self.job.issues_fixed = (
            fixed_issue_count
        )

        self.job.rows_removed = (
            statistics["rows_removed"]
        )

        self.job.cleaned_file.name = (
            f"cleaned/{csv_filename}"
        )

        self.job.status = (
            CleaningJob.Status.COMPLETED
        )

        self.job.completed_at = timezone.now()

        self._save_findings(
            statistics.get("findings", [])
        )

        self.job.save(
            update_fields=[
                "cleaned_file",
                "row_count",
                "issues_found",
                "issues_fixed",
                "rows_removed",
                "status",
                "completed_at",
                "updated_at",
            ]
        )

        if self.job.dataset:
            self.job.dataset.cleaned_file.name = (
                f"cleaned/{csv_filename}"
            )

            self.job.dataset.status = (
                Dataset.Status.CLEANED
            )

            self.job.dataset.save(
                update_fields=[
                    "cleaned_file",
                    "status",
                    "updated_at",
                ]
            )

    def _mark_failed(
        self,
        error_message: str,
    ) -> None:
        """Persist pipeline failure state."""

        self.job.status = (
            CleaningJob.Status.FAILED
        )

        self.job.error_message = (
            error_message
        )

        self.job.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )

        if self.job.dataset:
            self.job.dataset.status = (
                Dataset.Status.FAILED
            )

            self.job.dataset.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )
    def _save_findings(
        self,
        findings: list[dict],
    ) -> None:
        """Persist structured cleaning findings."""

        CleaningFinding.objects.filter(
            job=self.job
        ).delete()

        records = []

        for finding in findings:
            records.append(
                CleaningFinding(
                    job=self.job,
                    finding_type=finding["finding_type"],
                    column_name=finding.get(
                        "column_name",
                        "",
                    ),
                    description=finding["description"],
                    fixed=finding.get(
                        "fixed",
                        False,
                    ),
                )
            )

        if records:
            CleaningFinding.objects.bulk_create(
                records
            )
