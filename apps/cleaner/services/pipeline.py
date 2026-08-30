from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.cleaner.models import (
    CleaningFinding,
    CleaningJob,
    CleaningJobOutput,
)
from apps.cleaner.services.cleaner import clean_dataframe
from apps.datasets.services.lifecycle import DatasetLifecycleService
from apps.exporter.services import ExportService
from apps.importer.services import ImportService


class CleaningPipeline:
    """
    Production orchestration layer for DataPilot cleaning.

    Pipeline:

        original file
            ↓
        ImportService
            ↓
        pandas DataFrame
            ↓
        cleaning engine
            ↓
        cleaned DataFrame + statistics
            ↓
        ExportService
            ↓
        CSV + XLSX + PDF
            ↓
        CleaningJobOutput
            ↓
        completed CleaningJob
            ↓
        cleaned Dataset

    The pipeline is deliberately format-independent.

    Input format decisions belong to ImportService.
    Cleaning decisions belong to the cleaning engine.
    Output format decisions belong to ExportService.
    This class coordinates those components.
    """

    def __init__(self, job: CleaningJob) -> None:
        self.job = job
        self.importer = ImportService()
        self.exporter = ExportService()

    # PUBLIC API
    def run(self) -> dict:
        """
        Execute the complete cleaning pipeline.

        Returns:
            A dictionary containing the cleaned DataFrame,
            cleaning statistics, and generated output paths.

        Raises:
            Exception:
                The original pipeline exception is re-raised after
                failure state has been persisted.
        """

        try:
            self._mark_processing()

            dataframe = self._load_dataframe()

            cleaned_dataframe, statistics = clean_dataframe(
                dataframe
            )

            output_paths = self._export_results(
                cleaned_dataframe
            )

            with transaction.atomic():
                self._persist_outputs(output_paths)

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
            self._mark_failed(
                str(exc)
            )
            raise

    # IMPORT
    def _load_dataframe(self) -> pd.DataFrame:
        """
        Import the original uploaded file into a DataFrame.
        """

        if not self.job.original_file:
            raise ValueError(
                "Cleaning job does not have an original file."
            )

        file_path = self.job.original_file.path
        filename = self.job.original_file.name

        result = self.importer.read(
            file_path=file_path,
            filename=filename,
        )

        dataframe = result.dataframe

        if dataframe is None:
            raise ValueError(
                "Importer returned no DataFrame."
            )

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(
                "Importer returned an invalid DataFrame result."
            )

        return dataframe

    # EXPORT
    def _export_results(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, str]:
        """
        Export the cleaned DataFrame into DataPilot's standard outputs.

        Current standard outputs:

            <name>_cleaned.csv
            <name>_cleaned.xlsx
            <name>_cleaning_report.pdf
        """

        if dataframe is None:
            raise ValueError(
                "Cannot export a missing DataFrame."
            )

        if not self.job.original_file:
            raise ValueError(
                "Cleaning job does not have an original file."
            )

        cleaned_dir = (
            Path(settings.MEDIA_ROOT)
            / "cleaned"
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

        xlsx_filename = (
            f"{base_name}_cleaned.xlsx"
        )

        pdf_filename = (
            f"{base_name}_cleaning_report.pdf"
        )

        csv_path = (
            cleaned_dir
            / csv_filename
        )

        xlsx_path = (
            cleaned_dir
            / xlsx_filename
        )

        pdf_path = (
            cleaned_dir
            / pdf_filename
        )

        # CSV
        self.exporter.export(
            dataframe,
            csv_path,
            "csv",
        )

        # Excel
        self.exporter.export(
            dataframe,
            xlsx_path,
            "xlsx",
        )

        # PDF report
        self.exporter.export(
            dataframe,
            pdf_path,
            "pdf",
            original_filename=original_filename,
        )

        # Verify physical outputs
        output_paths = {
            "csv_path": csv_path,
            "xlsx_path": xlsx_path,
            "pdf_path": pdf_path,
        }

        for output_type, path in output_paths.items():
            if not path.is_file():
                raise FileNotFoundError(
                    f"Exporter did not create expected "
                    f"{output_type}: {path}"
                )

        return {
            "csv_filename": csv_filename,
            "xlsx_filename": xlsx_filename,
            "pdf_filename": pdf_filename,
            "csv_path": str(csv_path),
            "xlsx_path": str(xlsx_path),
            "pdf_path": str(pdf_path),
        }

    # OUTPUT PERSISTENCE
    def _persist_outputs(
        self,
        output_paths: dict[str, str],
    ) -> None:
        """
        Replace the job's previous output records with the new
        authoritative output set.
        """

        CleaningJobOutput.objects.filter(
            job=self.job
        ).delete()

        definitions = [
            {
                "file_format": CleaningJobOutput.Format.CSV,
                "path": output_paths["csv_path"],
                "filename": output_paths["csv_filename"],
                "content_type": "text/csv",
            },
            {
                "file_format": CleaningJobOutput.Format.XLSX,
                "path": output_paths["xlsx_path"],
                "filename": output_paths["xlsx_filename"],
                "content_type": (
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            },
            {
                "file_format": CleaningJobOutput.Format.PDF,
                "path": output_paths["pdf_path"],
                "filename": output_paths["pdf_filename"],
                "content_type": "application/pdf",
            },
        ]

        for definition in definitions:
            path = Path(
                definition["path"]
            )

            if not path.is_file():
                raise FileNotFoundError(
                    "Cannot persist missing cleaning output: "
                    f"{path}"
                )

            relative_path = (
                path
                .relative_to(settings.MEDIA_ROOT)
                .as_posix()
            )

            CleaningJobOutput.objects.create(
                job=self.job,
                file=relative_path,
                file_format=definition["file_format"],
                filename=definition["filename"],
                content_type=definition["content_type"],
            )

    # PROCESSING STATE
    def _mark_processing(self) -> None:
        """
        Move the job and associated dataset into processing state.
        """

        self.job.status = (
            CleaningJob.Status.PROCESSING
        )

        self.job.error_message = ""
        self.job.completed_at = None

        self.job.save(
            update_fields=[
                "status",
                "error_message",
                "completed_at",
                "updated_at",
            ]
        )

        if self.job.dataset:
            DatasetLifecycleService.start_processing(
                self.job.dataset
            )

    # COMPLETION
    def _mark_complete(
        self,
        *,
        statistics: dict,
        csv_filename: str,
    ) -> None:
        """
        Persist the successful cleaning result.
        """

        missing_values = int(
            statistics.get(
                "missing_values",
                0,
            )
        )

        duplicates_removed = int(
            statistics.get(
                "duplicates_removed",
                0,
            )
        )

        empty_rows_removed = int(
            statistics.get(
                "empty_rows_removed",
                0,
            )
        )

        rows_removed = int(
            statistics.get(
                "rows_removed",
                0,
            )
        )

        issues_fixed = (
            missing_values
            + duplicates_removed
            + empty_rows_removed
        )

        self.job.row_count = int(
            statistics.get(
                "original_rows",
                0,
            )
        )

        self.job.issues_found = issues_fixed
        self.job.issues_fixed = issues_fixed
        self.job.rows_removed = rows_removed

        self.job.cleaned_file.name = (
            f"cleaned/{csv_filename}"
        )

        self.job.status = (
            CleaningJob.Status.COMPLETED
        )

        self.job.error_message = ""

        self.job.completed_at = (
            timezone.now()
        )

        self._save_findings(
            statistics.get(
                "findings",
                [],
            )
        )

        self.job.save(
            update_fields=[
                "cleaned_file",
                "row_count",
                "issues_found",
                "issues_fixed",
                "rows_removed",
                "status",
                "error_message",
                "completed_at",
                "updated_at",
            ]
        )

        if self.job.dataset:
            self.job.dataset.cleaned_file.name = (
                f"cleaned/{csv_filename}"
            )

            self.job.dataset.save(
                update_fields=[
                    "cleaned_file",
                    "updated_at",
                ]
            )

            DatasetLifecycleService.mark_cleaned(
                self.job.dataset
            )

    # FAILURE
    def _mark_failed(
        self,
        error_message: str,
    ) -> None:
        """
        Persist a failed pipeline state.

        Failure handling is defensive so that an error while updating
        lifecycle state never hides the original pipeline exception.
        """

        try:
            self.job.status = (
                CleaningJob.Status.FAILED
            )

            self.job.error_message = (
                error_message
            )

            self.job.completed_at = None

            self.job.save(
                update_fields=[
                    "status",
                    "error_message",
                    "completed_at",
                    "updated_at",
                ]
            )

        except Exception:
            pass

        if self.job.dataset:
            try:
                DatasetLifecycleService.mark_failed(
                    self.job.dataset,
                    error_message,
                )
            except Exception:
                pass

    # FINDINGS
    def _save_findings(
        self,
        findings: list[dict],
    ) -> None:
        """
        Replace the job's previous findings with the latest
        authoritative findings.
        """

        CleaningFinding.objects.filter(
            job=self.job
        ).delete()

        records: list[CleaningFinding] = []

        for finding in findings:
            finding_type = finding.get(
                "finding_type"
            )

            description = finding.get(
                "description"
            )

            if not finding_type:
                raise ValueError(
                    "Cleaning finding is missing "
                    "'finding_type'."
                )

            if not description:
                raise ValueError(
                    "Cleaning finding is missing "
                    "'description'."
                )

            records.append(
                CleaningFinding(
                    job=self.job,
                    finding_type=finding_type,
                    column_name=finding.get(
                        "column_name",
                        "",
                    ),
                    row_number=finding.get(
                        "row_number"
                    ),
                    description=description,
                    fixed=bool(
                        finding.get(
                            "fixed",
                            False,
                        )
                    ),
                )
            )

        if records:
            CleaningFinding.objects.bulk_create(
                records
            )
